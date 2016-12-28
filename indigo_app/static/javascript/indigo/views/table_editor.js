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

      this.ckeditor = null;
      // setup CKEditor
      CKEDITOR.disableAutoInline = true;
      // make TH and TD editable
      CKEDITOR.dtd.$editable.th = 1;
      CKEDITOR.dtd.$editable.td = 1;
    },

    saveEdits: function(e) {
      var table = this.tableToAkn(this.editor.table),
          oldTable = this.view.documentContent.xmlDocument.getElementById(this.editor.table.id);

      this.editor.table.parentElement.contentEditable = "false";
      this.setTable(null);

      // update DOM
      this.view.documentContent.replaceNode(oldTable, [table]);
      this.view.sourceEditor.render();
    },

    tableToAkn: function(table) {
      var self = this,
          xml = new XMLSerializer().serializeToString(table);
      table = $.parseXML(xml).documentElement;
      // for some reason, we must remove the xmlns attribute and then re-set it
      table.removeAttribute("xmlns");
      table.setAttribute("xmlns", this.view.documentContent.xmlDocument.documentElement.namespaceURI);

      _.each(table.querySelectorAll("[contenteditable]"), function(n) {
        n.removeAttribute("contenteditable");
      });

      _.each(table.querySelectorAll(".selected"), function(n) {
        $(n).removeClass("selected");
      });

      _.each(table.querySelectorAll("[class]"), function(n) {
        if (n.className === "") n.removeAttribute("class");
      });

      // TODO: remove tbody and tfoot

      // transform br to eol
      _.each(table.querySelectorAll("br"), function(br) {
        br.parentElement.replaceChild(self.editor.renameNode(br, "eol"), br);
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
        for (var node = cell.childNodes[0]; node; node = next) {
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
      table.parentElement.contentEditable = "false";

      // nuke the active ckeditor instance, if any
      if (this.ckeditor) {
        this.ckeditor.destroy(true);
        this.ckeditor = null;
      }

      // undo changes
      table.parentElement.replaceChild(initialTable, table);
    },

    setTable: function(table) {
      var self = this;

      if (this.editor.table == table)
        return;

      if (table) {
        // cancel existing edit
        if (this.editor.table) {
          this.cancelEdits();
        }

        this.initialTable = table.cloneNode(true);
        var container = table.parentElement;

        $(table).closest('.table-editor-wrapper').addClass('table-editor-active');
        container.contentEditable = "true";
        this.$('.table-editor-buttons').show();

        // attach the CKEditor to the wrapper div
        this.ckeditor = CKEDITOR.inline(container);
        this.ckeditor.on('contentDom', function(e) {
          var table = self.ckeditor.element.$.firstElementChild;

          // TODO: ckeditor strips id from the table elem
          table.id = self.initialTable.id;

          self.editor.setTable(table);
          self.editor.cells[0][0].focus();
        });
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
      this.editor.insertRow(this.editor.activeCoords[1] + this.editor.activeCell.rowSpan);
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
