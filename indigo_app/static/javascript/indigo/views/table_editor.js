(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // The TableEditorView handles inline editing of tables.
  Indigo.TableEditorView = Backbone.View.extend({
    el: '#content-tab',
    events: {
      'click .table-insert-row-above': 'insertRowAbove',
      'click .table-insert-row-below': 'insertRowBelow',
      'click .table-insert-column-left': 'insertColumnLeft',
      'click .table-insert-column-right': 'insertColumnRight',
      'click .table-delete-row': 'deleteRow',
      'click .table-delete-column': 'deleteColumn',
      'click .table-merge-cells': 'mergeCells',
      'click .table-split-cells': 'splitCells',
      'click .table-toggle-heading': 'toggleHeading',
      'click .table-editor-wrapper .save-edit-table': 'saveEdits',
      'click .table-editor-wrapper .cancel-edit-table': 'cancelEdits',
    },

    initialize: function(options) {
      this.view = options.view;
      this.editor = new TableEditor();
      this.editor.onCellChanged = _.bind(this.cellChanged, this);
      this.tableWrapper = this.$('.table-editor-buttons .table-editor-wrapper').remove()[0];
    },

    saveEdits: function(e) {
      var table = this.tableToAkn(this.editor.table);
      // update DOM
      this.setTable(null);
    },

    tableToAkn: function(table) {
      var serializer = new XMLSerializer(),
          xml = serializer.serializeToString(table);
      table = $.parseXML(xml).documentElement;

      _.each(table.querySelectorAll("td, th"), function(n) {
        n.removeAttribute("contenteditable");
      });

      // transform akn-foo to <foo>
      // note that we do this bottom-up because we have to re-parse
      // XML as we're going
      var nodes = table.querySelectorAll('[class*="akn-"]');
      for (var i = nodes.length-1; i >= 0; i--) {
        var node = nodes[i],
            jump = node.tagName.length,
            aknClass = _.find(node.className.split(" "), function(c) {
              return c.startsWith("akn-");
            }),
            newTag = aknClass.substring(4);

        xml = serializer.serializeToString(node);
        xml = '<' + newTag + xml.substring(jump + 1, xml.length - jump - 1) + newTag + ">";
        xml = $.parseXML(xml).documentElement;

        xml.removeAttribute("xmlns");
        $(xml).removeClass(aknClass);
        if (xml.className === "")
          xml.removeAttribute("class");

        node.parentElement.replaceChild(xml, node);
      }

      // ensure direct children of td, th tags are wrapped in p tags
      _.each(table.querySelectorAll("td, th"), function(cell) {
        if (!cell.hasChildNodes) return;

        var lastP = null, next;
        for (var node = cell.childNodes[0]; node !== null; node = next) {
          next = node.nextSibling;

          if (node.nodeType == node.TEXT_NODE && node.textContent.trim() === "") {
            node.remove();
            continue;
          }

          if (node.tagName == 'p') {
            lastP = node;
          } else {
            if (lastP === null) {
              lastP = node.ownerDocument.createElement('p');
              node.parentElement.insertBefore(lastP, node);
            }

            lastP.appendChild(node);
          }
        }
      });

      return table;
    },

    cancelEdits: function(e) {
      if (!confirm("You'll lose you changes, are you sure?")) return;

      var table = this.editor.table,
          initialTable = this.initialTable;

      this.setTable(null);

      // undo changes
      table.parentElement.replaceChild(initialTable, table);
    },

    setTable: function(table) {
      if (this.editor.table == table)
        return;

      if (table) {
        // cancel existing edit
        if (this.editor.table) {
          self.cancelEdits();
        }

        $(table).closest('.table-editor-wrapper').addClass('table-editor-active');

        this.initialTable = table.cloneNode(true);
        this.editor.setTable(table);

        this.$('.table-editor-buttons').show();
        this.editor.cells[0][0].focus();
      } else {
        this.$('.table-editor-buttons').hide();
        this.editor.$table.closest('.table-editor-wrapper').removeClass('table-editor-active');

        this.editor.setTable(null);
        this.initialTable = null;
      }
    },

    cellChanged: function() {
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
