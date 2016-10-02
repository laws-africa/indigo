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
      var table = this.tableToAkn(this.editor.table),
          oldTable = this.view.documentContent.xmlDocument.getElementById(this.editor.table.id);

      this.setTable(null);

      // update DOM
      this.view.documentContent.replaceNode(oldTable, [table]);
      this.view.sourceEditor.render();
    },

    tableToAkn: function(table) {
      var xml = new XMLSerializer().serializeToString(table);
      table = $.parseXML(xml).documentElement;
      // for some reason, we must remove the xmlns attribute and then re-set it
      table.removeAttribute("xmlns");
      table.setAttribute("xmlns", this.view.documentContent.xmlDocument.documentElement.namespaceURI);

      _.each(table.querySelectorAll("[contenteditable]"), function(n) {
        n.removeAttribute("contenteditable");
      });

      // transform akn-foo to <foo>, going bottom-up
      var nodes = table.querySelectorAll('[class*="akn-"]');
      for (var i = nodes.length-1; i >= 0; i--) {
        var node = nodes[i],
            aknClass = _.find(node.className.split(" "), function(c) {
              return c.startsWith("akn-");
            }),
            newTag = aknClass.substring(4);

        var newNode = this.editor.renameNode(node, newTag);

        $(newNode).removeClass(aknClass);
        if (newNode.className === "")
          newNode.removeAttribute("class");

        node.parentElement.replaceChild(newNode, node);
      }

      // ensure direct children of td, th tags are wrapped in p tags
      _.each(table.querySelectorAll("td, th"), function(cell) {
        if (!cell.hasChildNodes) return;

        var lastP = null, next,
            first = true;
        for (var node = cell.childNodes[0]; node !== null; node = next) {
          next = node.nextSibling;

          // trim leading and trailing whitespace
          if ((first || next === null) && node.nodeType == node.TEXT_NODE && node.textContent.trim() === "") {
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

          first = false;
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
