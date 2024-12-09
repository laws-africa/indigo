/**
 * This class handles the text-based AKN editor. It is responsible for unparsing XML into text, re-parsing changed
 * text into XML, and handling text-based editor actions (like bolding, etc.).
 */
class AknTextEditor {
  constructor (root, document, onElementParsed) {
    this.root = root;
    this.document = document;
    this.previousText = null;
    this.xmlElement = null;
    this.onElementParsed = onElementParsed;
    // flag to prevent circular updates to the text
    this.updating = false;
    this.liveUpdates = false;

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
    this.root.querySelector('.insert-remark').addEventListener('click', (e) => this.insertRemark(e));
  }

  setXmlElement (element) {
    this.xmlElement = element;

    if (!this.updating) {
      this.previousText = this.unparse();
      this.monacoEditor.setValue(this.previousText);
      const top = {column: 1, lineNumber: 1};
      this.monacoEditor.setPosition(top);
      this.monacoEditor.revealPosition(top);
    }
  }

  async onTextChanged () {
    if (this.liveUpdates) {
      const text = this.monacoEditor.getValue();

      if (this.previousText !== text) {
        const elements = await this.parse();
        // check that the response is still valid
        if (text === this.monacoEditor.getValue()) {
          this.previousText = text;
          this.updating = true;
          this.onElementParsed(elements);
          this.updating = false;
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

  /** Parse the text in the editor into XML. Returns an array of new elements. */
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

    try {
      const xml = await this.bluebellParser.parse(
        text,
        this.document.get('expression_frbr_uri'),
        fragment,
        eidPrefix,
      );

      let newElement = $.parseXML(xml);
      if (fragmentRule === 'akomaNtoso') {
        // entire document
        return [newElement.documentElement];
      } else {
        return newElement.documentElement.children;
      }
    } catch (e) {
      Indigo.errorView.show(e);
    }

    return null;
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
  constructor(root, document, onElementParsed) {
    this.root = root;
    this.xmlElement = null;
    this.updating = false;
    this.visible = false;
    this.onElementParsed = onElementParsed;
    // this will be null if the user doesn't have perms
    this.tab = window.document.querySelector('button[data-bs-target="#xml-pane"]');
    this.documentContent = document.content;
    // TODO: do we still need this if the xmlElement is being set each time the DOM is updated?
    this.documentContent.on('change:dom', this.onDomChanged.bind(this));

    window.document.body.addEventListener('indigo:pane-toggled', this.onPaneToggled.bind(this));
    window.document.querySelector('.document-secondary-pane-nav').addEventListener(
      'shown.bs.tab', this.onNavTabChanged.bind(this)
    );
  }

  setXmlElement (element) {
    this.xmlElement = element;
    if (this.visible) {
      this.render();
    }
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
    const xml = prettyPrintXml(Indigo.toXml(this.xmlElement));
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

  onDomChanged () {
    // if the fragment has been swapped out, don't use a stale fragment; our parent will
    // call editFragment() to update our fragment
    if (this.visible && this.fragment && this.xmlElement.ownerDocument === this.documentContent.xmlDocument) {
      this.render();
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
    let element;

    try {
      console.log('Parsing changes to XML');
      element = $.parseXML(this.editor.getValue()).documentElement;
    } catch (err) {
      // squash errors
      console.log(err);
      return;
    }

    this.onElementParsed(element);
  }
}

window.Indigo.XMLEditor = XMLEditor;
