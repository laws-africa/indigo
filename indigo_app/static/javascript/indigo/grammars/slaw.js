(function(exports) {
  "use strict";

  exports.Indigo.grammars.registry.slaw = {
    setupEditor: function(editor) {
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
    }
  };
})(window);
