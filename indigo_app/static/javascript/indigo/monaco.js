(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.monaco = {
    /**
     * Wrap the current selection of the editor in pre and post text.
     * Expands the selection if there is selected text, or moves
     * the selection between pre and post if there is nothing selected.
     */
    wrapSelection: function(editor, id, pre, post) {
      const sel = editor.getSelection();
      const text = editor.getModel().getValueInRange(sel);
      const op = {
        identifier: id,
        range: sel,
        forceMoveMarkers: false,
        text: pre + text + post
      };
      // either extend the selection, or place cursor inside the tags
      const cursor = text.length === 0
        ? sel.setEndPosition(sel.startLineNumber, sel.startColumn + pre.length)
          .setStartPosition(sel.startLineNumber, sel.startColumn + pre.length)
        : sel.setEndPosition(sel.endLineNumber, sel.endColumn + 4);
      editor.executeEdits('indigo', [op], [cursor]);
    }
  };
})(window);
