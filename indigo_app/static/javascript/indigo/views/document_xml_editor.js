/**
 * This class handles the text-based AKN editor. It is responsible for unparsing XML into text, re-parsing changed
 * text into XML, and handling text-based editor actions (like bolding, etc.).
 */
class AknTextEditor {
  constructor (root, document, onSave, onDiscard) {
    this.root = root;
    this.document = document;
    this.onSave = onSave;
    this.onDiscard = onDiscard;
    this.editing = false;
    this.previousText = null;
    this.xmlElement = null;
    // copy of the original element being edited, for when changes are discarded
    this.xmlElementOriginal = null;
    this.dirty = false;
    // flag to prevent circular updates to the text
    this.updating = false;
    this.liveUpdates = true;
    // for provision mode (set to true if the top-level eId changes)
    this.reloadOnSave = false;

    document.content.on('mutation', this.onDocumentMutated.bind(this));

    this.grammarName = document.tradition().settings.grammar.name;
    this.grammarModel = new Indigo.grammars.registry[this.grammarName](document.get('frbr_uri'));
    this.grammarModel.setup();

    // get the appropriate remark style for the tradition
    this.remarkGenerator = Indigo.remarks[this.document.tradition().settings.remarkGenerator];

    this.setupMonacoEditor();
    this.setupToolbar();
    this.bluebellParser = new Indigo.BluebellParser(
      this.document.url() + '/parse',
      {
        'Content-Type': 'application/json; charset=utf-8',
        'X-CSRFToken': Indigo.csrfToken,
      }
    );
    this.bluebellParser.setup();
  }

  setupMonacoEditor () {
    const options = this.grammarModel.monacoOptions();
    options.automaticLayout = true;
    this.monacoEditor = window.monaco.editor.create(
      this.root.querySelector('.document-text-editor .monaco-editor-box'),
      options
    );
    this.grammarModel.setupEditor(this.monacoEditor);

    const onTextChanged = _.debounce(this.onTextChanged.bind(this), 500);
    this.monacoEditor.onDidChangeModelContent(onTextChanged);
  }

  setupToolbar () {
    for (const el of this.root.querySelectorAll('.editor-action')) {
      el.addEventListener('click', (e) => this.triggerEditorAction(e));
    }

    this.root.querySelector('.toggle-word-wrap').addEventListener('click', (e) => this.toggleWordWrap(e));
    this.root.querySelector('.insert-image').addEventListener('click', (e) => this.insertImage(e));
    for (const el of this.root.querySelectorAll('.insert-remark')) {
      el.addEventListener('click', (e) => this.insertRemark(e));
    }

    this.setLiveUpdates(this.liveUpdates);
    const checkbox = this.root.querySelector('#live-updates-chk');
    checkbox.addEventListener('change', (e) => {
      this.liveUpdates = e.currentTarget.checked;
      this.onTextChanged();
    });

    this.root.querySelector('.btn.save').addEventListener('click', this.acceptChanges.bind(this));
    this.root.querySelector('.btn.cancel').addEventListener('click', this.discardChanges.bind(this));
  }

  setLiveUpdates (liveUpdates) {
    this.liveUpdates = liveUpdates;
    this.root.querySelector('#live-updates-chk').checked = liveUpdates;
  }

  setXmlElement (element) {
    this.xmlElement = element;

    if (!this.editing) {
      this.editing = true;
      this.xmlElementOriginal = element;
      this.dirty = false;
    }

    this.previousText = this.unparse();

    // only default liveUpdates to true if the document isn't too long
    // a 100k document takes about 0.5s to parse, which is our upper limit
    this.setLiveUpdates(this.previousText.length < 100000);

    this.monacoEditor.setValue(this.previousText);
    const top = {column: 1, lineNumber: 1};
    this.monacoEditor.setPosition(top);
    this.monacoEditor.revealPosition(top);
  }

  async onTextChanged () {
    const text = this.monacoEditor.getValue();
    this.dirty = this.dirty || text !== this.previousText;

    if (this.liveUpdates && this.previousText !== text) {
      const elements = await this.parseSafely();
      if (elements !== false) {
        this.previousText = text;
        this.updating = true;
        try {
          this.replaceElement(elements);
        } finally {
          // clear the flag after the next event loop, which gives mutation events a chance to be dispatched
          setTimeout(() => {
            this.updating = false;
          }, 0);
        }
      }
    }
  }

  unparse () {
    if (!this.xmlElement) {
      return "";
    }

    try {
      return this.grammarModel.xmlToText(this.xmlElement);
    } catch (e) {
      // log details and then re-raise the error so that it's reported and we can work out what went wrong
      console.log("Error converting XML to text");
      console.log(this.xmlElement);
      console.log(new XMLSerializer().serializeToString(this.xmlElement));
      console.log(e);
      throw e;
    }
  }

  /**
   * Parse the text in the editor into XML. Returns an array of new elements.
   *
   * @returns {Promise<Element[]>} the new elements or an empty list if the text is empty
   * @throws {Error} if the text cannot be parsed
   **/
  async parse () {
    const text = this.monacoEditor.getValue();
    if (!text.trim()) {
      return [];
    }

    const fragmentRule = this.document.tradition().grammarRule(this.xmlElement);
    const eId = this.xmlElement.getAttribute('eId');
    let fragment = null;
    let eidPrefix = null;

    if (fragmentRule !== 'akomaNtoso') {
      fragment = fragmentRule;
      if (eId && eId.lastIndexOf('__') > -1) {
        // retain the eId of the parent element as the prefix
        eidPrefix = eId.substring(0, eId.lastIndexOf('__'));
      }
    }

    const xml = await this.bluebellParser.parse(
      text,
      this.document.get('expression_frbr_uri'),
      fragment,
      eidPrefix,
    );

    let newElement = Indigo.parseXml(xml);

    // if the top-level eId changed in provision mode, reload the page when saving later (just set the flag here)
    if (this.xmlElement.parentNode.tagName === 'portionBody') {
      // set it back to false if the eId is changed back before saving too
      this.reloadOnSave = newElement.firstChild.firstChild.getAttribute('eId') !== Indigo.Preloads.provisionEid;
    }

    if (fragmentRule === 'akomaNtoso') {
      // entire document
      return [newElement.documentElement];
    }

    return newElement.documentElement.children;
  }

  /**
   * Parse the text in the editor and ensure that it hasn't changed underneath us.
   * @returns {Promise<Element[]|boolean>}
   */
  async parseSafely () {
    const text = this.monacoEditor.getValue();

    try {
      const elements = await this.parse();
      // check that the response is still valid
      if (text === this.monacoEditor.getValue()) {
        return elements;
      }
    } catch (err) {
      Indigo.errorView.show(err);
    }

    return false;
  }

  /**
   * Accept the changes in the editor. This re-parses the text one last time and updates the DOM.
   */
  async acceptChanges () {
    if (!this.editing) return;

    if (!this.liveUpdates) {
      const btn = this.root.querySelector('.btn.save');
      btn.setAttribute('disabled', 'true');

      try {
        const elements = await this.parseSafely();
        if (elements === false) {
          return;
        }
        this.replaceElement(elements);
      } finally {
        btn.removeAttribute('disabled');
      }
    }

    this.editing = false;
    this.dirty = false;
    this.xmlElement = this.xmlElementOriginal = null;
    this.onSave();
  }

  /**
   * Discard the changes in the editor and, if the XML element has changed, replace it with the original.
   */
  discardChanges () {
    if (this.editing) {
      // only replace the element with the original if it has changed through us
      if (this.dirty && this.xmlElement && this.xmlElement !== this.xmlElementOriginal) {
        this.replaceElement([this.xmlElementOriginal]);
      }
      this.editing = false;
      this.dirty = false;
      this.onDiscard();
    }
  }

  /**
   * Replace the current XML element with the given elements.
   */
  replaceElement (elements) {
    if (this.xmlElement) {
      if (elements && elements.length) {
        // regular update
        this.document.content.replaceNode(this.xmlElement, elements);
      } else if (this.xmlElement.parentNode.tagName === 'portionBody') {
        // we can't delete the whole provision in portion mode
        alert($t('You cannot delete the whole provision in provision editing mode.'));
      } else if (confirm($t('Go ahead and delete this provision from the document?'))) {
        // remove element
        this.document.content.replaceNode(this.xmlElement, null);
      }

    }
  }

  /**
   * The XML document has changed, re-render if it impacts our xmlElement.
   *
   * @param model documentContent model
   * @param mutation a MutationRecord object
   */
  onDocumentMutated (model, mutation) {
    if (!this.editing) return;

    switch (model.getMutationImpact(mutation, this.xmlElement)) {
      case 'replaced':
        this.xmlElement = mutation.addedNodes[0];
        // fall through to 'changed'
      case 'changed':
        if (!this.updating) {
          // the XML has changed, update the text in the editor
          this.previousText = this.unparse();
          const posn = this.monacoEditor.getPosition();
          this.monacoEditor.setValue(this.previousText);
          this.monacoEditor.setPosition(posn);
        }
        break;
      case 'removed':
        console.log('Mutation removes AknTextEditor.xmlElement from the tree');
        this.discardChanges();
        break;
    }
  }

  toggleWordWrap (e) {
    const wordWrap = this.monacoEditor.getOption(132);
    this.monacoEditor.updateOptions({wordWrap: wordWrap === 'off' ? 'on' : 'off'});
    if (e.currentTarget.tagName === 'BUTTON') {
      e.currentTarget.classList.toggle('active');
    }
  }

  insertImage (e) {
    if (!this.insertImageBox) {
      // setup insert-image box
      this.insertImageBox = new Indigo.InsertImageView({document: this.document});
    }

    let image = this.grammarModel.getImageAtCursor(this.monacoEditor);
    let selected = null;

    if (image) {
      let filename = image.src;
      if (filename.startsWith("media/")) filename = filename.substring(6);
      selected = this.document.attachments().findWhere({filename: filename});
    }

    this.insertImageBox.show((image) => {
      this.grammarModel.insertImageAtCursor(this.monacoEditor, 'media/' + image.get('filename'));
      this.monacoEditor.focus();
    }, selected);
  }

  insertRemark (e) {
    const amendedSection = this.xmlElement.id.replace('-', ' ');
    const verb = e.currentTarget.getAttribute('data-verb');
    const amendingWork = this.getAmendingWork();
    let remark = '<remark>';

    if (this.remarkGenerator && amendingWork) {
      remark = this.remarkGenerator(this.document, amendedSection, verb, amendingWork, this.grammarModel);
    }

    this.grammarModel.insertRemark(this.monacoEditor, remark);
    this.monacoEditor.focus();
  }

  triggerEditorAction (e) {
    // an editor action from the toolbar
    e.preventDefault();
    const action = e.currentTarget.getAttribute('data-action');
    this.monacoEditor.focus();
    this.monacoEditor.trigger('indigo', action);
  }

  getAmendingWork () {
    const date = this.document.get('expression_date');
    const documentAmendments = Indigo.Preloads.amendments;
    const amendment = documentAmendments.find((a) => a.date === date);
    if (amendment) {
      return amendment.amending_work;
    }
  }
}

window.Indigo.AknTextEditor = AknTextEditor;

/**
 * The XMLEditor manages a monaco editor for editing XML.
 */
class XMLEditor {
  constructor(root, document) {
    this.root = root;
    this.xmlElement = null;
    this.updating = false;
    this.visible = false;
    // this will be null if the user doesn't have perms
    this.tab = window.document.querySelector('button[data-bs-target="#xml-pane"]');
    this.document = document;
    this.document.content.on('mutation', this.onDomMutated.bind(this));

    window.document.body.addEventListener('indigo:pane-toggled', this.onPaneToggled.bind(this));
    window.document.querySelector('.document-secondary-pane-nav').addEventListener(
      'shown.bs.tab', this.onNavTabChanged.bind(this)
    );
  }

  setXmlElement (element) {
    this.xmlElement = element;
    this.render();
  }

  show() {
    this.visible = true;
    this.setupXmlEditor();
    this.render();
  }

  hide() {
    this.visible = false;
  }

  render() {
    // pretty-print the xml
    if (this.visible) {
      const xml = this.xmlElement ? prettyPrintXml(Indigo.toXml(this.xmlElement)) : '';
      if (this.editor.getValue() !== xml) {
        const posn = this.editor.getPosition();

        // ignore the onDidChangeModelContent event triggered by setValue
        this.updating = true;
        this.editor.setValue(xml);
        this.updating = false;

        this.editor.setPosition(posn);
        this.editor.layout();
      }
    }
  }

  setupXmlEditor() {
    if (!this.editor) {
      this.editor = window.monaco.editor.create(this.root.querySelector('.monaco-editor-box'), {
        automaticLayout: true,
        codeLens: false,
        detectIndentation: false,
        foldingStrategy: 'indentation',
        language: 'xml',
        lineDecorationsWidth: 0,
        lineNumbersMinChars: 3,
        roundedSelection: false,
        scrollBeyondLastLine: false,
        showFoldingControls: 'always',
        tabSize: 2,
        wordWrap: 'on',
        theme: 'vs',
        wrappingIndent: 'same',
      });

      const onEditorChanged = _.debounce(this.onEditorChanged.bind(this), 500);
      this.editor.onDidChangeModelContent(() => {
        if (!this.updating) onEditorChanged();
      });
    }
  }

  /**
   * The XML document has changed, re-render if it impacts our xmlElement.
   *
   * @param model documentContent model
   * @param mutation a MutationRecord object
   */
  onDomMutated (model, mutation) {
    switch (model.getMutationImpact(mutation, this.xmlElement)) {
      case 'replaced':
        this.xmlElement = mutation.addedNodes[0];
        this.render();
        break;
      case 'changed':
        this.render();
        break;
      case 'removed':
        // the change removed xmlElement from the tree
        console.log('Mutation removes SourceEditor.xmlElement from the tree');
        this.xmlElement = null;
        this.render();
        break;
    }
  }

  onNavTabChanged(e) {
    if (e.target.dataset.bsTarget === '#xml-pane') {
      this.show();
    } else {
      this.hide();
    }
  }

  onPaneToggled(e) {
    if (e.detail.pane === 'document-secondary-pane' && this.tab) {
      if (e.detail.visible) {
        // the pane is visible AND the tab is visible
        if (this.tab.classList.contains('active')) {
          this.show();
        }
      } else {
        // a pane was toggled, we're no longer visible, stop our work
        this.hide();
      }
    }
  }

  onEditorChanged() {
    const text = this.editor.getValue().trim();
    if (text) {
      let doc;
      try {
        console.log('Parsing changes to XML');
        doc = Indigo.parseXml(text);
      } catch (err) {
        // squash errors
        console.log(err);
        return;
      }
      this.document.content.replaceNode(this.xmlElement, [doc.documentElement]);
    }
  }
}

window.Indigo.XMLEditor = XMLEditor;
