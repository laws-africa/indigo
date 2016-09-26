(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // The TableEditorView handles inline editing of tables.
  Indigo.TableEditorView = Backbone.View.extend({
    el: '#content-tab',
    events: {
      // TODO handle table btn bar clicks
      // TODO handle save
      // TODO: hande cancel
      'click .ig.table-wrapper .edit': 'editTable',
    },

    initialize: function(options) {
      this.view = options.view;
      this.editor = new TableEditor();
      this.editor.onCellChanged = _.bind(this.cellChanged, this);
    },

    editTable: function(e) {
      this.setTable(this.nextElementSibling);
    },

    setTable: function(table) {
      // TODO: start editing a table
      // TODO: cancel editing other table?
      if (this.editor.table != table)
        this.editor.setTable(table);
    },

    cellChanged: function() {
      // TODO: toggle toolbar buttons
    },

    addRowBelow: function() {
      if (!self.editor.activeCell) return;
      self.editor.insertRow(self.editor.activeCoords[1] + 1);
    },

    addColumnRight: function(e) {
      e.preventDefault();
      if (!self.editor.activeCell) return;
      self.editor.insertColumn(self.editor.activeCoords[0] + 1);
    },

    deleteRow: function(e) {
      e.preventDefault();
      if (!self.editor.activeCell) return;

      self.editor.removeRow(self.editor.activeCoords[1]);
      // TODO update the active cell
    },

    deleteColumn: function(e) {
      e.preventDefault();
      if (!self.editor.activeCell) return;

      self.editor.removeColumn(self.editor.activeCoords[0]);
      // update the active cell
    },
  });
})(window);
