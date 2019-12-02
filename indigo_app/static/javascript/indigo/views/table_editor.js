(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /* The TableEditorView handles inline editing of tables.
   * It works in conjunction with CKEditor and the standalone TableEditor
   * support script. CKEditor provides the actual editing support and
   * enforces decent HTML. The TableEditor script treats the table like
   * an Excel spreadsheet and allows adding rows, merging cells, etc.
   */
  Indigo.TableEditorView = Backbone.View.extend({
    el: 'body',
    events: {
      'click .table-insert-row-above': 'insertRowAbove',
      'click .table-insert-row-below': 'insertRowBelow',
      'click .table-insert-column-left': 'insertColumnLeft',
      'click .table-insert-column-right': 'insertColumnRight',
      'click .table-delete-row': 'deleteRow',
      'click .table-delete-column': 'deleteColumn',
      'click .table-merge-cells': 'toggleMergeCells',
      'click .table-toggle-heading': 'toggleHeading',
      'click .save-edit-table': 'saveChanges',
      'click .cancel-edit-table': 'discardChanges',
    },

    initialize: function(options) {
      var self = this;

      this.parent = options.parent;
      this.documentContent = options.documentContent;
      this.editor = new TableEditor();
      this.editor.onSelectionChanged = _.bind(this.selectionChanged, this);
      this.editor.onCellChanged = _.bind(this.cellChanged, this);
      this.tableWrapper = this.$('.table-editor-buttons .table-editor-wrapper').remove()[0];
      this.editing = false;

      this.ckeditor = null;
      // setup CKEditor
      CKEDITOR.disableAutoInline = true;
      // make TH and TD editable
      CKEDITOR.dtd.$editable.th = 1;
      CKEDITOR.dtd.$editable.td = 1;

      // setup transforms
      var htmlTransform = new XSLTProcessor();
      $.get('/static/xsl/html_to_akn.xsl')
        .then(function(xml) {
          htmlTransform.importStylesheet(xml);
          self.htmlTransform = htmlTransform;
        });
    },

    saveChanges: function(e) {
      if (!this.editing) return;

      var table,
          width = this.table.clientWidth,
          oldTable = this.documentContent.xmlDocument.getElementById(this.table.getAttribute('data-id'));

      table = $.parseHTML(this.ckeditor.getData())[0];
      if (table.tagName != 'TABLE') table = table.querySelector('table');

      // stop editing
      // TODO: what does this do with the changed content?
      this.ckeditor.destroy();
      this.ckeditor = null;
      this.editTable(null);

      // get new xml
      table = this.tableToAkn(table);

      // update DOM
      this.documentContent.replaceNode(oldTable, [table]);
      this.parent.render();
    },

    tableToAkn: function(table) {
      if (!this.htmlTransform) return null;

      // html -> string -> xhtml so that the XML is well formed
      var xml = $.parseXML(new XMLSerializer().serializeToString(table));

      // xhtml -> akn
      xml = this.htmlTransform.transformToFragment(xml.firstChild, this.documentContent.xmlDocument);

      // strip whitespace at start of first p tag in table cells
      xml.querySelectorAll('table td > p:first-child, table th > p:first-child').forEach(function(p) {
        var text = p.firstChild;

        if (text && text.nodeType == text.TEXT_NODE) {
          text.textContent = text.textContent.replace(/^\s+/, '');
        }
      });

      // strip whitespace at end of last p tag in table cells
      xml.querySelectorAll('table td > p:last-child, table th > p:last-child').forEach(function(p) {
        var text = p.lastChild;

        if (text && text.nodeType == text.TEXT_NODE) {
          text.textContent = text.textContent.replace(/\s+$/, '');
        }
      });

      return xml;
    },

    discardChanges: function(e, force) {
      if (!this.editing) return;
      if (!force && !confirm("You'll lose your changes, are you sure?")) return;

      var table = this.editor.table,
          initialTable = this.initialTable;

      //this.editTable(null);

      // nuke the active ckeditor instance, if any
      if (this.ckeditor) {
        this.ckeditor.destroy(true);
        this.ckeditor = null;
      }

      // undo changes
      table.parentElement.replaceChild(initialTable, table);
    },

    // start editing an HTML table
    editTable: function(table) {
      var self = this;

      // TODO this.table is the html table as ckeditor sees it, whereas 'table' is an HTML table before ckeditor has wrapped it
      if (this.table == table)
        return;

      if (table) {
        // cancel existing edit
        if (this.table) {
          this.discardChanges(null, true);
        }

        this.observers = [];
        this.initialTable = table.cloneNode(true);
        $(table).closest('.table-editor-wrapper').addClass('table-editor-active');

        var editable = table.parentElement;
        editable.contentEditable = true;

        CKEDITOR.on('instanceReady', function(evt) {
          evt.removeListener();
          self.table = editable.querySelector('table');
          self.manageTableWidth(self.table);
          //self.editor.setTable(editable.firstElementChild);
        });

        this.ckeditor = CKEDITOR.inline(editable, {
          enterMode: CKEDITOR.ENTER_BR,
          shiftEnterMode: CKEDITOR.ENTER_BR,
          toolbar: [],
          allowedContent: 'a[!data-href,!href]; img[!src,!data-src]; span(akn-remark); span(akn-p); ' +
                          'table[id, data-id]; thead; tbody; tr; th{width}[colspan,rowspan]; td{width}[colspan,rowspan]; p;',
        });

        this.editing = true;
        this.trigger('start');
      } else {
        // clean up observers
        this.observers.forEach(function(observer) { observer.disconnect(); });
        this.observers = [];

        this.$(table).closest('.table-editor-wrapper').removeClass('table-editor-active');

        //this.editor.setTable(null);
        this.initialTable = null;

        this.editing = false;
        this.trigger('finish');
      }
    },

    /* Set up observers to:
     * 1. ensure that the table width isn't changed
     * 2. change pixel-based column widths to percentages
     */
    manageTableWidth: function(table) {
      // Discard fixed pixel widths on the table itself. This are applied by CKEditor's
      // table resizer.
      var observer = new MutationObserver(function(mutations, observer) {
        for (var i = 0; i < mutations.length; i++) {
          var mutation = mutations[i];

          // discard fixed pixel widths
          if (mutation.target.style.width) {
            mutation.target.style.removeProperty('width');
          }
        }
      });
      observer.observe(table, {attributes: true, attributeFilter: ['style']});
      this.observers.push(observer);

      // change pixel width columns to percentages
      observer = new MutationObserver(function(mutations, observer) {
        for (var i = 0; i < mutations.length; i++) {
          var mutation = mutations[i],
              tag = mutation.target.tagName;

          if ((tag === 'TD' || tag === 'TH') && mutation.target.style.width.slice(-2) == "px") {
            mutation.target.style.setProperty(
              'width',
              parseInt(mutation.target.style.width.slice(0, -2)) / table.clientWidth * 100 + '%');
          }
        }
      });
      observer.observe(table, {subtree: true, attributes: true, attributeFilter: ['style']});
      this.observers.push(observer);
    },

    cellChanged: function() {
      return;

      // cell has changed, unbind and re-bind editor
      if (this.ckeditor) {
        this.ckeditor.element.$.contentEditable = false;
        this.ckeditor.destroy();
      }

      this.editor.activeCell.contentEditable = true;
      this.ckeditor = CKEDITOR.inline(this.editor.activeCell, {
        removePlugins: 'toolbar',
        enterMode: CKEDITOR.ENTER_BR,
        shiftEnterMode: CKEDITOR.ENTER_BR,
        allowedContent: 'a[!data-href,!href]; img[!src,!data-src]; span(akn-remark)',
      });
    },

    selectionChanged: function() {
      var selected = this.editor.getSelectedCells(),
          merged = _.any(selected, function(c) { return c.colSpan > 1 || c.rowSpan > 1; }),
          headings = _.any(selected, function(c) { return c.tagName == 'TH'; });

      $('.table-merge-cells')
        .prop('disabled', !merged && selected.length < 2)
        .toggleClass('active', merged);

      $('.table-toggle-heading').toggleClass('active', headings);
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

    toggleMergeCells: function(e) {
      var merged = _.any(this.editor.getSelectedCells(), function(c) { return c.colSpan > 1 || c.rowSpan > 1; });

      if (merged) {
        this.editor.splitSelection();
      } else {
        this.editor.mergeSelection();
        this.selectionChanged();
      }
    },

    toggleHeading: function(e) {
      var self = this,
          selection = this.editor.getSelectedCells();

      var heading = _.any(selection, function(c) { return c.tagName == 'TH'; });
      _.each(selection, function(c) {
        self.editor.toggleHeading(c, !heading);
      });

      this.selectionChanged();
    },
  });
})(window);
