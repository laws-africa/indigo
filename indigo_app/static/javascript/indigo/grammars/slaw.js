(function(exports) {
  "use strict";

  class SlawGrammarModel {
    image_re = /!\[([^\]]*)]\(([^)]*)\)/g;

    /**
     * Setup the grammar for a particular document model.
     */
    setup (model) {
      // setup akn to text transform
      const self = this;
      // TODO: don't use jquery
      $.get(model.url() + '/static/xsl/text.xsl').then(function (xml) {
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
      editor.addAction({
        id: 'format.bold',
        label: 'Format Bold',
        keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_B],
        run: function(editor) {
          Indigo.monaco.wrapSelection(editor, 'format.bold', '**', '**');
          editor.pushUndoStop();
        }
      });

      editor.addAction({
        id: 'format.italics',
        label: 'Format Italics',
        keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_I],
        run: function(editor) {
          Indigo.monaco.wrapSelection(editor, 'format.italics', '//', '//');
          editor.pushUndoStop();
        }
      });

      editor.addAction({
        id: 'format.remark',
        label: 'Format Remark',
        run: function(editor) {
          Indigo.monaco.wrapSelection(editor, 'format.remark', '[[', ']]');
          editor.pushUndoStop();
        }
      });

      editor.addAction({
        id: 'insert.schedule',
        label: 'Insert Schedule',
        run: function(editor) {
          const sel = editor.getSelection();
          const cursor = sel.setEndPosition(sel.startLineNumber + 1, 12 + 24)
            .setStartPosition(sel.startLineNumber + 1, 12);

          editor.executeEdits('indigo', [{
            identifier: 'insert.schedule',
            range: sel,
            forceMoveMarkers: false,
            text: '\nSCHEDULE - <optional schedule name>\n<optional schedule title>\n\n',
          }], [cursor]);
          editor.pushUndoStop();
        }
      });

      editor.addAction({
        id: 'insert.table',
        label: 'Insert Table',
        run: function (editor) {
          let table;
          const sel = editor.getSelection();

          if (sel.isEmpty()) {
            table = ["", "{|", "|-", "! heading 1", "! heading 2", "|-", "| cell 1", "| cell 2", "|-", "| cell 3", "| cell 4", "|-", "|}", ""].join("\n");
          } else {
            var lines = editor.getModel().getValueInRange(sel).split("\n");
            table = "\n{|\n|-\n";
            lines.forEach(function(line) {
              // ignore empty lines
              if (line.trim() !== "") {
                table = table + "| " + line + "\n|-\n";
              }
            });
            table = table + "|}\n";
          }

          const cursor = sel.setEndPosition(sel.startLineNumber + 3, 3)
            .setStartPosition(sel.startLineNumber + 3, 3);

          editor.executeEdits('indigo', [{
            identifier: 'insert.table',
            range: sel,
            forceMoveMarkers: false,
            text: table,
          }], [cursor]);
          editor.pushUndoStop();
        }
      });
    }

    insertRemark (editor, remark) {
      const sel = editor.getSelection();
      editor.executeEdits('indigo', [{
        identifier: 'insert.remark',
        range: sel,
        forceMoveMarkers: false,
        text: this.markupRemark(remark),
      }]);
      editor.pushUndoStop();
    }

    /**
     * Markup a textual remark
     */
    markupRemark (text) {
      return `[[${text}]]`;
    }

    /**
     * Markup a link (ref)
     */
    markupRef (title, href) {
      return `[${title}](${href})`;
    }

    /**
     * Get the image filename at the cursor, if any.
     */
    getImageAtCursor (editor) {
      const match = this.getMatchAtCursor(editor, this.image_re);
      if (match) {
        // return the filename
        return match[2];
      }
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
     * Insert or update the image at the current cursor
     */
    insertImageAtCursor (editor, filename) {
      const match = this.getMatchAtCursor(editor, this.image_re);
      let sel = editor.getSelection();
      let image;

      if (match) {
        // update existing image
        image = `![${match[1]}](${filename})`;
        sel = sel.setEndPosition(sel.startLineNumber, match.index + match[0].length + 1);
        sel = sel.setStartPosition(sel.startLineNumber, match.index + 1);
      } else {
        // insert new image
        image = `![](${filename})`;
      }

      editor.executeEdits('indigo', [{
        identifier: 'insert.remark',
        range: sel,
        forceMoveMarkers: false,
        text: image,
      }]);

      editor.pushUndoStop();
    }

    /**
     * Paste these (clean) XML tables into the editor.
     */
    pasteTables (editor, tables) {
      const text = [];

      for (let i = 0; i < tables.length; i++) {
        text.push(this.xmlToText(tables[i]));
      }

      editor.executeEdits('indigo', [{
        identifier: 'insert.table',
        range: editor.getSelection(),
        text: text.join('\n'),
      }]);
      editor.pushUndoStop();
    }
  }

  exports.Indigo.grammars.registry.slaw = new SlawGrammarModel();
})(window);
