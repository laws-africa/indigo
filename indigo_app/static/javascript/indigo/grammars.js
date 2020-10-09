(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Base class for grammar models.
   */
  class GrammarModel {
    constructor (frbrUri, xslUrl) {
      this.frbrUri = frbrUri;
      this.xslUrl = xslUrl;
      this.language_id = null;
      this.language_def = {};
      this.theme_id = null;
      this.theme_def = {
        base: 'vs',
        inherit: true,
      };
    }

    monacoOptions () {
      this.installLanguage();

      return {
        codeLens: false,
        detectIndentation: false,
        foldingStrategy: 'indentation',
        language: this.language_id,
        lineDecorationsWidth: 0,
        lineNumbersMinChars: 3,
        roundedSelection: false,
        scrollBeyondLastLine: false,
        showFoldingControls: 'always',
        tabSize: 2,
        wordWrap: 'on',
        theme: this.theme_id,
        wrappingIndent: 'same',
      };
    }

    /**
     * Setup the grammar for a particular document model.
     */
    setup () {
      // setup akn to text transform
      const self = this;
      // TODO: don't use jquery
      $.get(this.xslUrl).then(function (xml) {
        const textTransform = new XSLTProcessor();
        textTransform.importStylesheet(xml);
        self.textTransform = textTransform;
      });
    }

    /**
     * Unparse an XML element into a string.
     */
    xmlToText (element) {
      return this.textTransform
        .transformToFragment(element, document)
        .firstChild.textContent
        // remove multiple consecutive blank lines
        .replace(/^( *\n){2,}/gm, "\n");
    }

    /**
     * Configure a new instance of a Monaco editor.
     */
    setupEditor (editor) {
      this.installActions(editor);
    }

    installLanguage () {
      monaco.languages.register({ id: this.language_id });
      monaco.languages.setMonarchTokensProvider(this.language_id, this.language_def);
      monaco.editor.defineTheme(this.theme_id, this.theme_def);
    }

    /**
     * Install named actions on the editor. Subclasses should install at least these actions:
     *
     * * format.bold
     * * format.italics
     * * format.remork
     * * insert.schedule
     * * insert.table
     *
     * @param editor monaco editor instance
     */
    installActions (editor) {
    }

    /**
     * Markup a textual remark
     */
    markupRemark (text) {
    }

    /**
     * Markup a link (ref)
     */
    markupRef (title, href) {
    }

    /**
     * Markup an image
     */
    markupImage (title, src) {
    }

    insertRemark (editor, remark) {
      const sel = editor.getSelection();
      editor.executeEdits(this.language_id, [{
        identifier: 'insert.remark',
        range: sel,
        text: this.markupRemark(remark),
      }]);
      editor.pushUndoStop();
    }

    /**
     * Get a description of the image at the cursor, if any.
     */
    getImageAtCursor (editor) {
      const match = this.getMatchAtCursor(editor, this.image_re);
      if (match) {
        return {
          match: match,
        };
      }
    }

    /**
     * Insert or update the image at the current cursor
     */
    insertImageAtCursor (editor, filename) {
      const existing = this.getImageAtCursor(editor);
      let sel = editor.getSelection();
      let image;

      if (existing) {
        // update existing image
        image = this.markupImage(existing.title, filename);
        sel = sel.setEndPosition(sel.startLineNumber, existing.match.index + existing.match[0].length + 1);
        sel = sel.setStartPosition(sel.startLineNumber, existing.match.index + 1);
      } else {
        // insert new image
        image = this.markupImage('', filename);
      }

      editor.executeEdits(this.language_id, [{
        identifier: 'insert.image',
        range: sel,
        text: image,
      }]);

      editor.pushUndoStop();
    }

    /**
     * Returns the match object, if any, for a regular expression match at the current cursor position,
     * on the current line.
     */
    getMatchAtCursor (editor, regexp) {
      const sel = editor.getSelection();
      const line = editor.getModel().getLineContent(sel.startLineNumber);

      for (let match of line.matchAll(regexp)) {
        if (match.index <= sel.startColumn && sel.startColumn <= match.index + match[0].length) {
          return match;
        }
      }
    }

    /**
     * Paste these (clean) XML tables into the editor.
     */
    pasteTables (editor, tables) {
      const text = [];

      for (let i = 0; i < tables.length; i++) {
        text.push(this.xmlToText(tables[i]));
      }

      editor.executeEdits(this.language_id, [{
        identifier: 'insert.table',
        range: editor.getSelection(),
        text: text.join('\n'),
      }]);
      editor.pushUndoStop();
    }
  }

  Indigo.grammars = {
    GrammarModel: GrammarModel,
    registry: {}
  };
})(window);
