(function(exports) {
  "use strict";

  class SlawGrammarModel {
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

    markupRemark (text) {
      return `[[${text}]]`;
    }

    markupRef (title, href) {
      return `[${title}](${href})`;
    }

    /**
     * Get the image filename at the cursor, if any.
     */
    getImageAtCursor (editor) {
    }

    /**
     * Insert or update the image at the current cursor
     */
    insertImageAtCursor (editor, filename) {
    }
  }

  exports.Indigo.grammars.registry.slaw = new SlawGrammarModel();
})(window);
