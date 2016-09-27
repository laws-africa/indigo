(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // The TableEditorView handles inline editing of tables.
  Indigo.TableEditorView = Backbone.View.extend({
    el: '#content-tab',
    events: {
      // TODO handle save
      // TODO: hande cancel
      'click .ig.table-wrapper .edit': 'editTable',
      'click .table-insert-row-above': 'insertRowAbove',
      'click .table-insert-row-below': 'insertRowBelow',
      'click .table-insert-column-left': 'insertColumnLeft',
      'click .table-insert-column-right': 'insertColumnRight',
      'click .table-delete-row': 'deleteRow',
      'click .table-delete-column': 'deleteColumn',
      'click .table-merge-cells': 'mergeCells',
      'click .table-split-cells': 'splitCells',
      'click .table-toggle-heading': 'toggleHeading',
    },

    initialize: function(options) {
      // TODO: handle "save"
      // TODO: handle "cancel" editing
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
      $('.table-toggle-heading').toggleClass('active', this.editor.activeCell && this.editor.activeCell.tagName == 'TH');
    },

    insertRowAbove: function() {
      if (!this.editor.activeCell) return;
      this.editor.insertRow(this.editor.activeCoords[1]);
    },

    insertRowBelow: function() {
      if (!this.editor.activeCell) return;
      this.editor.insertRow(this.editor.activeCoords[1] + 1);
    },

    insertColumnLeft: function(e) {
      if (!this.editor.activeCell) return;
      this.editor.insertColumn(this.editor.activeCoords[0]);
    },

    insertColumnRight: function(e) {
      if (!this.editor.activeCell) return;
      this.editor.insertColumn(this.editor.activeCoords[0] + 1);
    },

    deleteRow: function(e) {
      if (!this.editor.activeCell) return;

      this.editor.removeRow(this.editor.activeCoords[1]);
      // TODO update the active cell
    },

    deleteColumn: function(e) {
      if (!this.editor.activeCell) return;

      this.editor.removeColumn(this.editor.activeCoords[0]);
      // update the active cell
    },

    mergeCells: function(e) {
      this.editor.mergeSelection();
    },

    splitCells: function(e) {
      this.editor.splitSelection();
    },

    toggleHeading: function(e) {
      this.editor.toggleHeading();
    },
  });
})(window);
