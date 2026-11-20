(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /* The TableEditorView handles inline editing of tables.
   * CKEditor provides the actual editing support and enforces decent HTML.
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
      'change .table-toggle-border': 'toggleBorder',
      'click .table-text-left': 'alignTextLeft',
      'click .table-text-center': 'alignTextCenter',
      'click .table-text-right': 'alignTextRight',
      'click .table-text-justify': 'alignTextJustify',
      'click .table-text-default': 'alignTextDefault',
      'change .table-format-select': 'changeFormat',
      'click .table-format-action': 'changeFormat',
      'change .table-remove-padding': 'changePadding',
      'click .table-text-bold': 'toggleTextBold',
      'click .table-text-italic': 'toggleTextItalic',
      'click .table-text-underline': 'toggleTextUnderline',
      'click .save-edit-table': 'saveChanges',
      'click .cancel-edit-table': 'discardChanges',
    },

    initialize: function(options) {
      this.parent = options.parent;
      this.documentContent = options.documentContent;
      this.documentContent.on('mutation', this.onDomMutated.bind(this));
      this.tableWrapper = this.$('.table-editor-wrapper').removeClass('d-none').remove()[0];
      this.editing = false;
      this.aknElement = document.querySelector('.document-primary-pane-content-pane la-akoma-ntoso');

      this.ckeditor = null;
      // setup CKEditor
      CKEDITOR.disableAutoInline = true;
      // make TH and TD editable
      CKEDITOR.dtd.$editable.th = 1;
      CKEDITOR.dtd.$editable.td = 1;
      this.ckeditorConfig = {
        enterMode: CKEDITOR.ENTER_BR,
        shiftEnterMode: CKEDITOR.ENTER_BR,
        coreStyles_bold: {element: 'b', overrides: 'strong'},
        coreStyles_italic: {element: 'i', overrides: 'em'},

        // Enable these formatting buttons, but css in _documents.scss hides the toolbar.
        // This allows us to place our own toolbar buttons that use this functionalty.
        toolbar: [{ name: 'basicstyles', items: [ 'Bold', 'Italic', 'Underline'] }],

        // this must align with the elements and attributes supported by indigo-akn
        // https://github.com/laws-africa/indigo-akn/blob/master/src/xsl.js
        allowedContent: 'a[!data-href,!href]; img[!src,!data-src]; span(*)[data-eid];' +
                        'b; i; u; p(*)[data-eid];' +
                        'sup; sub;' +
                        'table(*)[id,data-eid]; thead; tbody; tr;' +
                        'th(*){width}[colspan,rowspan];' +
                        'td(*){width}[colspan,rowspan];',
      };
    },

    makeTablesEditable: function(html) {
      for (const table of html.querySelectorAll('table[id]')) {
        const w = this.tableWrapper.cloneNode(true);

        w.querySelector('button').dataset.tableId = table.id;
        table.insertAdjacentElement('beforebegin', w);
        // we bind the CKEditor instance to this div, since CKEditor can't be
        // directly attached to the table element
        w.querySelector('.table-container').append(table);
      }
    },

    /**
     * Can we edit this html table? Tables with complex content can't be edited with this editor.
     */
    canEditTable: function(table) {
      const oldTable = this.documentContent.getElementByScopedId(table.id);
      if (oldTable) {
        // look for complex content
        const result = this.documentContent.xpath('.//a:authorialNote | .//a:blockList | .//a:ul | .//a:ol | .//a:embeddedStructure', oldTable);
        return result.snapshotLength === 0;
      }
      return true;
    },

    /**
     * The XML document has changed, re-render if it impacts our table element.
     *
     * @param model documentContent model
     * @param mutations an array of MutationRecord objects
     */
    onDomMutated (model, mutations) {
      if (!this.editing) return;

      // process each mutation in order; we stop processing after finding the first one that significantly impacts us
      for (const mutation of mutations) {
        switch (model.getMutationImpact(mutation, this.table)) {
          case 'replaced':
            this.discardChanges(true);
            return;
          case 'changed':
            this.discardChanges(true);
            return;
          case 'removed':
            // the change removed xmlElement from the tree
            console.log('Mutation removes TableEditor.table from the tree');
            this.discardChanges(true);
            return;
        }
      }
    },

    saveChanges: function(e) {
      if (!this.editing || !this.table) return;

      var table,
          oldTable = this.documentContent.getElementByScopedId(this.table.id),
          html;

      html = $.parseHTML(this.ckeditor.getData()) || [];
      for (var i = 0; i < html.length; i++) {
        table = html[i];
        if (table.tagName !== 'TABLE') table = table.querySelector('table');
        if (table) break;
      }

      // stop editing
      this.editTable(null);

      if (table) {
        // get new xml
        table = indigoAkn.htmlToAkn(table);
      }

      if (table) {
        table.querySelectorAll('table').forEach(this.removeRedundantColspans.bind(this));
        // Retain the legacy PDF-only override from source XML. It is not
        // exposed to HTML, CKEditor or the HTML-to-AKN converter.
        if (oldTable && oldTable.hasAttribute('fontsize')) {
          table.firstElementChild.setAttribute('fontsize', oldTable.getAttribute('fontsize'));
        }
        // update DOM
        this.documentContent.replaceNode(oldTable, [table]);
      } else {
        // remove the table
        this.documentContent.replaceNode(oldTable, null);
      }

      this.parent.render();
      this.trigger('save');
    },

    removeRedundantColspans: function(table) {
      var plan = Indigo.TableLayout.fromTable(table).plan();
      if (!plan) return;
      var rows = Array.from(table.children).filter(function(el) { return el.localName === 'tr'; });
      var group = Array.from(table.children).find(function(el) { return el.localName === 'colgroup'; });
      if (group && plan.compact_widths.length < plan.columns) {
        group.replaceChildren();
        plan.compact_widths.forEach(function(width) {
          var col = table.ownerDocument.createElementNS(table.namespaceURI, 'col');
          col.setAttribute('width', width + '%');
          group.appendChild(col);
        });
      }
      plan.cells.forEach(function(placement) {
        var cells = Array.from(rows[placement.row].children).filter(function(el) { return el.localName === 'td' || el.localName === 'th'; });
        var cell = cells[placement.index];
        if (placement.colspan === 1) cell.removeAttribute('colspan');
        else cell.setAttribute('colspan', placement.colspan);
        if (plan.compact_widths.length < plan.columns) {
          // Width styles are already supported throughout the editing round trip.
          // Save every visible cell's width so later PDF planning reconstructs
          // the same (possibly unequal) compacted column widths.
          var style = (cell.getAttribute('style') || '').split(';').filter(function(part) { return part.trim() && !/^\s*width\s*:/i.test(part); });
          style.push('width: ' + placement.width + '%');
          cell.setAttribute('style', style.join('; ') + ';');
        }
      });
    },

    discardChanges: function(force) {
      if (!this.editing || !this.table) return;
      if (!force && !confirm($t("You'll lose your changes, are you sure?"))) return;

      var editable = this.editable,
          originalTable = this.originalTable;

      this.editTable(null);

      // undo changes
      $(editable).empty();
      editable.appendChild(originalTable);
      this.trigger('discard');
    },

    // start editing an HTML table
    editTable: function(table) {
      var self = this;

      if (this.table === table) return;

      if (table) {
        // cancel existing edit
        if (this.table) {
          this.discardChanges(null, true);
        }

        // disable other table edit buttons
        for (const el of this.aknElement.querySelectorAll('.edit-table')) {
          el.disabled = true;
        }

        this.observers = [];

        // Re-render the table and edit that version. This means that we have the original,
        // including any event handlers that other components may have attached to its content.
        // If the edit is cancelled, this is swapped back into place.
        // Re-rendering the table ensures we're not editing any elements that the editor has
        // added, such as annotations.
        this.originalTable = table;
        table = this.parent.htmlRenderer.renderXmlElement(
          this.documentContent.document, this.documentContent.getElementByScopedId(table.id)
        ).firstElementChild;
        this.originalTable.parentElement.replaceChild(table, this.originalTable);

        $(table).closest('.table-editor-wrapper').addClass('table-editor-active');

        this.editable = table.parentElement;
        this.editable.contentEditable = 'true';

        CKEDITOR.on('instanceReady', function(evt) {
          evt.removeListener();
          self.table = self.editable.querySelector('table');
          if (!self.table) {
            throw "CKEditor ready, but no table in editable. " + table.id;
          }
          self.manageTableWidth(self.table);
          self.updateToolbar();
        });

        // remove foreign content
        $(this.editable).find(window.indigoAkn.foreignElementsSelector).remove();
        this.ckeditor = CKEDITOR.inline(this.editable, this.ckeditorConfig);
        this.setupCKEditorInstance(this.ckeditor);

        this.editing = true;
      } else {
        // clean up observers
        this.observers.forEach(function(observer) { observer.disconnect(); });
        this.observers = [];

        this.editable.contentEditable = 'false';
        $(this.editable).closest('.table-editor-wrapper').removeClass('table-editor-active');

        this.ckeditor.destroy();
        this.ckeditor = null;

        this.originalTable = null;
        this.table = null;
        this.editable = null;
        this.editing = false;
        // enable all table edit buttons
        for (const el of this.aknElement.querySelectorAll('.edit-table')) {
          el.disabled = false;
        }
        this.trigger('finish');
      }
    },

    setupCKEditorInstance: function(ckeditor) {
      var self = this;

      // watch selection change
      ckeditor.on('selectionChange', _.bind(this.selectionChanged, this));

      // watch for style changes
      ckeditor.attachStyleStateChange(new CKEDITOR.style({element: 'b'}), function(state) {
          self.styleStateChanged('bold', state === CKEDITOR.TRISTATE_ON);
        });
      ckeditor.attachStyleStateChange(new CKEDITOR.style({element: 'i'}), function(state) {
          self.styleStateChanged('italic', state === CKEDITOR.TRISTATE_ON);
        });
      ckeditor.attachStyleStateChange(new CKEDITOR.style({element: 'u'}), function(state) {
        self.styleStateChanged('underline', state === CKEDITOR.TRISTATE_ON);
      });
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

          if ((tag === 'TD' || tag === 'TH') && mutation.target.style.width.slice(-2) === "px") {
            mutation.target.style.setProperty(
              'width',
              parseInt(mutation.target.style.width.slice(0, -2)) / table.clientWidth * 100 + '%');
          }
        }
      });
      observer.observe(table, {subtree: true, attributes: true, attributeFilter: ['style']});
      this.observers.push(observer);
    },

    selectionChanged: function(evt) {
      var selected = this.getSelectedCells(),
          merged = _.any(selected, function(c) { return c.colSpan > 1 || c.rowSpan > 1; }),
          headings = _.any(selected, function(c) { return c.tagName === 'TH'; });

      $('.table-merge-cells').toggleClass('active', merged);
      $('.table-toggle-heading').toggleClass('active', headings);

      this.updateToolbar();
    },

    updateToolbar: function() {
      if (!this.table || !this.editable) return;
      var toolbar = this.editable.closest('.table-editor-wrapper');
      if (!toolbar) return;
      var selected = this.getSelectedCells(),
          alignment = {};

      // toggle alignment buttons
      selected.forEach(function(cell) {
        var value = this.getFormat(cell, 'alignment') || 'default';
        alignment[value] = (alignment[value] || 0) + 1;
      }, this);

      $(toolbar).find('.table-text-left, .table-text-center, .table-text-right, .table-text-justify, .table-text-default').removeClass('active');
      alignment = _.keys(alignment);
      if (alignment.length === 1) $(toolbar).find('.table-text-' + alignment[0]).addClass('active');

      var borderControl = toolbar.querySelector('.table-toggle-border');
      // Older editor versions stored this whole-table PDF control on cells.
      borderControl.checked = this.table.classList.contains('akn--no-border') ||
        Array.from(this.table.querySelectorAll('td.akn--no-border, th.akn--no-border')).some(function(cell) {
          return cell.closest('table') === this.table;
        }, this);
      toolbar.querySelectorAll('.table-format-select').forEach(function(select) {
        var elements = select.dataset.formatTarget === 'table' ? [this.table] : selected;
        var values = Array.from(new Set(elements.map(function(el) { return this.getFormat(el, select.dataset.format); }, this)));
        select.value = values.length > 1 ? '__mixed' : (values[0] || '');
        select.disabled = elements.length === 0;
      }, this);
      var sizes = Array.from(new Set(selected.map(function(cell) { return this.getFormat(cell, 'size'); }, this)));
      var mixed = sizes.length > 1;
      var currentSize = sizes[0] || '';
      toolbar.querySelectorAll('.table-format-action').forEach(function(action) {
        var active = selected.length > 0 && !mixed && action.value === currentSize;
        action.classList.toggle('active', active);
        action.setAttribute('aria-pressed', active ? 'true' : 'false');
        if (action.value === currentSize && !mixed) toolbar.querySelector('.table-cell-size-label').textContent = action.textContent;
      });
      var mixedLabel = toolbar.querySelector('.table-cell-size-mixed');
      mixedLabel.classList.toggle('d-none', !mixed);
      if (mixed) toolbar.querySelector('.table-cell-size-label').textContent = mixedLabel.textContent;
      toolbar.querySelector('.table-remove-padding').checked = this.table.classList.contains('akn--no-padding');
      toolbar.querySelectorAll('[data-selected-cells]').forEach(function(control) { control.disabled = selected.length === 0; });
    },

    formatValues: {
      size: ['normal', 'small', 'xsmall', 'xxsmall'],
      alignment: ['left', 'center', 'right', 'justify'],
    },

    getFormat: function(element, kind) {
      return this.formatValues[kind].find(function(value) {
        return element.classList.contains('akn--text-' + value);
      }) || '';
    },

    setFormat: function(element, kind, value) {
      this.formatValues[kind].forEach(function(name) { element.classList.remove('akn--text-' + name); });
      if (this.formatValues[kind].includes(value)) element.classList.add('akn--text-' + value);
    },

    changeFormat: function(e) {
      var control = e.currentTarget;
      this.editFormatting(function() {
        var elements = control.dataset.formatTarget === 'table' ? [this.table] : this.getSelectedCells();
        elements.forEach(function(el) { this.setFormat(el, control.dataset.format, control.value); }, this);
      });
    },

    changePadding: function(e) {
      this.editFormatting(function() { this.table.classList.toggle('akn--no-padding', e.currentTarget.checked); });
    },

    editFormatting: function(callback) {
      if (!this.table || !this.ckeditor) return;
      this.ckeditor.fire('saveSnapshot');
      callback.call(this);
      this.ckeditor.fire('saveSnapshot');
      this.ckeditor.fire('change');
      this.updateToolbar();
    },

    alignCells: function(value) {
      this.editFormatting(function() {
        this.getSelectedCells().forEach(function(cell) { this.setFormat(cell, 'alignment', value); }, this);
      });
    },

    insertRowAbove: function() {
      this.ckeditor.execCommand("rowInsertBefore");
    },

    insertRowBelow: function() {
      this.ckeditor.execCommand("rowInsertAfter");
    },

    insertColumnLeft: function(e) {
      this.ckeditor.execCommand("columnInsertBefore");
    },

    insertColumnRight: function(e) {
      this.ckeditor.execCommand("columnInsertAfter");
    },

    deleteRow: function(e) {
      if (this.table.rows.length > 1) this.ckeditor.execCommand("rowDelete");
    },

    deleteColumn: function(e) {
      // there needs to be at least one row with more than one column
      var okay = false;

      for (var i = 0; i < this.table.rows.length; i++) {
        if (this.table.rows[i].cells.length > 1 || this.table.rows[i].cells[0].colSpan > 1) {
          okay = true;
          break;
        }
      }

      if (okay) this.ckeditor.execCommand("columnDelete");
    },

    toggleMergeCells: function(e) {
      var self = this,
          cells = this.getSelectedCells(),
          merged = _.any(cells, function(c) { return c.colSpan > 1 || c.rowSpan > 1; });

      if (merged) {
        cells.forEach(function(cell) {
          self.ckeditor.getSelection().selectElement(new CKEDITOR.dom.element(cell));
          if (cell.colSpan > 1) self.ckeditor.execCommand("cellVerticalSplit");
          if (cell.rowSpan > 1) self.ckeditor.execCommand("cellHorizontalSplit");
        });
      } else {
        this.ckeditor.execCommand("cellMerge");
      }
    },

    toggleHeading: function(e) {
      var self = this,
          cells = this.getSelectedCells(),
          makeHeading = !_.any(cells, function(c) { return c.tagName === 'TH'; });

      cells.forEach(function(cell) {
        if (cell.tagName === 'TH' && makeHeading) return;
        if (cell.tagName === 'TD' && !makeHeading) return;
        if (!cell.parentElement) return;

        cell.parentElement.replaceChild(
          self.renameNode(cell, makeHeading ? 'th' : 'td'),
          cell);
      });
    },

    toggleBorder: function(e) {
      var removeBorders = e.currentTarget.checked;
      this.editFormatting(function() {
        this.table.classList.toggle('akn--no-border', removeBorders);
        // Consolidate legacy cell flags only when the user changes this setting.
        this.table.querySelectorAll('td.akn--no-border, th.akn--no-border').forEach(function(cell) {
          if (cell.closest('table') === this.table) cell.classList.remove('akn--no-border');
        }, this);
      });
    },

    alignTextCenter: function(e) {
      this.alignCells('center');
    },

    alignTextRight: function(e) {
      this.alignCells('right');
    },

    alignTextLeft: function(e) {
      this.alignCells('left');
    },

    alignTextJustify: function() { this.alignCells('justify'); },
    alignTextDefault: function() { this.alignCells(''); },

    toggleTextBold: function(e) {
      this.ckeditor.execCommand('bold');
    },

    toggleTextItalic: function(e) {
      this.ckeditor.execCommand('italic');
    },

    toggleTextUnderline: function(e) {
      this.ckeditor.execCommand('underline');
    },

    styleStateChanged: function(style, active) {
      this.$('.table-text-' + style).toggleClass('active', active);
    },

    renameNode: function(node, newname) {
      var newnode = node.ownerDocument.createElement(newname),
        attrs = node.attributes;

      for (var i = 0; i < attrs.length; i++) {
        newnode.setAttribute(attrs[i].name, attrs[i].value);
      }

      while (node.childNodes.length > 0) {
        newnode.appendChild(node.childNodes[0]);
      }

      return newnode;
    },

    getSelectedCells: function() {
      if (!this.table) return [];

      var cells = Array.from(this.table.querySelectorAll('.cke_table-faked-selection'));

      if (!cells.length) {
        // selection is the currently active cell
        var selection = this.ckeditor && this.ckeditor.getSelection();
        var ranges = selection ? selection.getRanges() : [];
        if (ranges.length) {
          var cell = ranges[0].startContainer.getAscendant({th: 1, td: 1}, true);
          if (cell) cells = [cell.$];
        }
      }

      return cells;
    },
  });
})(window);
