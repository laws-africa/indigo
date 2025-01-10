(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * The SourceEditorView manages rendering and editing (via text, xml or table editors) of an xml element. It handles
   * rendering itself and coordination between the editors, but editors themselves are responsible for updating the
   * document DOM.
   *
   * It can have two active xml elements, which are only different in quick edit mode:
   *
   * - the one being rendered (xmlElement)
   * - the one being edited (aknTextEditor.xmlElement)
   */
  Indigo.SourceEditorView = Backbone.View.extend({
    el: 'body',
    events: {
      'click .text-editor-buttons .btn.save': 'acceptChanges',
      'click .text-editor-buttons .btn.cancel': 'discardChanges',
      'click .btn.edit-text': 'fullEdit',
      'click .btn.edit-table': 'editTable',
      'click .quick-edit': 'quickEdit',
      'click .btn.show-structure': 'toggleShowStructure',
      'click .show-pit-comparison': 'toggleShowComparison',
      'mouseenter la-akoma-ntoso .akn-ref[href^="#"]': 'refPopup',
    },

    initialize: function(options) {
      this.name = 'source';
      this.document = this.model;
      this.xmlElement = null;
      this.quickEditTemplate = $('<a href="#" class="quick-edit"><i class="fas fa-pencil-alt"></i></a>')[0];
      this.contentPane = document.querySelector('.document-primary-pane-content-pane');
      this.sheetInner = this.contentPane.querySelector('.document-workspace .document-sheet-container .sheet-inner');
      this.aknElement = this.contentPane.querySelector('la-akoma-ntoso');
      this.toolbar = document.querySelector('.document-toolbar-wrapper');

      this.aknTextEditor = new Indigo.AknTextEditor(
        this.el,
        this.document,
        true,
      );

      const xmlEditorBox = document.querySelector('.document-xml-editor');
      this.xmlEditor = xmlEditorBox ? new Indigo.XMLEditor(
        xmlEditorBox,
        this.document,
      ) : null;

      this.tocView = options.tocView;
      this.tocView.selection.on('change', this.onTocSelectionChanged, this);

      this.listenTo(this.document, 'change', this.onDocumentChanged);
      this.listenTo(this.document.content, 'mutation', this.onDomMutated);

      // setup table editor
      this.tableEditor = new Indigo.TableEditorView({parent: this, documentContent: this.document.content});
      this.tableEditor.on('start', this.onTableEditStart, this);
      this.tableEditor.on('finish', this.onTableEditFinish, this);
      this.tableEditor.on('discard', this.editActivityCancelled, this);
      this.tableEditor.on('save', this.editActivityEnded, this);

      // setup renderer
      this.editorReady = $.Deferred();
      this.setupRenderers();
    },

    setupRenderers: function() {
      var self = this;

      // setup akn to html transform
      this.htmlRenderer = Indigo.render.getHtmlRenderer(this.document);
      this.htmlRenderer.ready.then(function() {
        self.editorReady.resolve();
      });
    },

    setComparisonDocumentId: function(id) {
      this.comparisonDocumentId = id;
      this.render();
    },

    fullEdit: function() {
      this.editXmlElement(this.xmlElement);
    },

    quickEdit: function(e) {
      const htmlElement = e.currentTarget.parentElement.parentElement;
      const elemId = htmlElement.id;
      const element = this.document.content.xmlDocument.querySelector('[eId="' + elemId + '"]');

      if (element && this.confirmAndDiscardChanges()) {
        this.editXmlElement(element);

        this.contentPane.querySelector('.quick-editing')?.classList.remove('quick-editing');
        htmlElement.classList.add('quick-editing');

        // scroll it almost (but not quite) to the top
        htmlElement.style.scrollMarginTop = '10px';
        htmlElement.scrollIntoView({behavior: "smooth"});
      }
    },

    /**
     * Edit the given XML element in the text editor.
     */
    editXmlElement: function(element) {
      const editing = this.aknTextEditor.editing;

      this.aknTextEditor.setXmlElement(element);
      if (this.xmlEditor) this.xmlEditor.setXmlElement(element);

      // if we weren't already editing, activate the editor
      if (!editing) {
        this.editActivityStarted('text');
        this.toggleTextEditor(true);
        this.aknTextEditor.monacoEditor.focus();
        this.toolbar.classList.add('is-editing', 'edit-mode-text');
      }
    },

    /**
     * If we're currently editing, check if the user is happy to discard changes. If they are,
     * discard and return true, otherwise return false.
     *
     * If the user is not editing, return true.
     */
    confirmAndDiscardChanges: function() {
      if (this.isDirty()) {
        if (confirm($t("You will lose your changes, are you sure?"))) {
          this.discardChanges();
        } else {
          return false;
        }
      }

      return true;
    },

    /**
     * End the edit activity and save the changes made (in text or table edit modes).
     */
    acceptChanges: async function() {
      // save table edits, if any
      this.tableEditor.saveChanges();

      if (this.aknTextEditor.editing) {
        const btn = this.toolbar.querySelector('.text-editor-buttons .btn.save');
        btn.setAttribute('disabled', 'true');

        try {
          if (await this.aknTextEditor.acceptChanges()) {
            this.editActivityEnded();
            this.closeTextEditor();
          }
        } finally {
          btn.removeAttribute('disabled');
        }
      }
    },

    /**
     * Discard the content of all editors.
     */
    discardChanges: function() {
      if (this.aknTextEditor.editing) {
        this.editActivityCancelled();
        this.closeTextEditor();
      }
      this.tableEditor.discardChanges(true);
      this.aknTextEditor.discardChanges();
    },

    closeTextEditor: function(e) {
      this.toggleTextEditor(false);
      this.aknElement.querySelector('.quick-editing')?.classList.remove('quick-editing');
      this.toolbar.classList.remove('is-editing', 'edit-mode-text');
      // set the xml edit back to using the visible element, in case quick edit was used
      if (this.xmlEditor) this.xmlEditor.setXmlElement(this.xmlElement);
    },

    /**
     * Set the XML element that is currently being shown.
     */
    showXmlElement: function(element) {
      if (this.xmlElement !== element) {
        this.xmlElement = element;

        if (this.aknTextEditor.editing) {
          // we're in edit mode, so update the element being edited
          this.editXmlElement(element);
        } else {
          if (this.xmlEditor) this.xmlEditor.setXmlElement(element);
        }

        this.render();
        this.contentPane.scrollTo(0, 0);
      }
    },

    onTocSelectionChanged: function(selection) {
      if (selection && this.xmlElement !== selection.get('element')) {
        this.discardChanges();
        this.showXmlElement(selection.get('element'));
      }
    },

    onDocumentChanged: function() {
      this.coverpageCache = null;
      this.render();
    },

    /**
     * The XML document has changed, re-render if it impacts our xmlElement.
     *
     * @param model documentContent model
     * @param mutation a MutationRecord object
     */
    onDomMutated: function(model, mutation) {
      switch (model.getMutationImpact(mutation, this.xmlElement)) {
        case 'replaced':
          this.xmlElement = mutation.addedNodes[0];
          this.render();
          break;
        case 'changed':
          this.render();
          break;
        case 'removed':
          // the change removed xmlElement from the tree
          console.log('Mutation removes SourceEditor.xmlElement from the tree');
          this.discardChanges();
          break;
      }
    },

    editActivityStarted: function(mode) {
    },

    editActivityEnded: function() {
    },

    editActivityCancelled: function() {
    },

    render: function() {
      if (!this.xmlElement) return;

      this.sheetInner.classList.toggle('is-fragment', this.xmlElement.parentElement !== null);

      var self = this,
          renderCoverpage = this.xmlElement.parentElement === null && Indigo.Preloads.provisionEid === "",
          coverpage;

      this.aknElement.classList.add('spinner-when-empty');
      this.aknElement.replaceChildren();

      if (renderCoverpage) {
        coverpage = document.createElement('div');
        coverpage.className = 'spinner-when-empty';
        this.aknElement.appendChild(coverpage);
        this.renderCoverpage().then(function(nodes) {
          for (const node of nodes) {
            coverpage.append(node);
          }
          self.trigger('rendered');
        });
      }

      this.htmlRenderer.ready.then(function() {
        var html = self.htmlRenderer.renderXmlElement(self.document, self.xmlElement);

        self.makeLinksExternal(html);
        self.addWorkPopups(html);
        self.makeTablesEditable(html);
        self.makeElementsQuickEditable(html);
        self.highlightQuickEditElement(html);
        self.aknElement.appendChild(html);

        self.trigger('rendered');
        self.renderComparisonDiff();
      });
    },

    renderComparisonDiff: function() {
      var self = this,
          data = {};

      if (!this.comparisonDocumentId) return;

      data.document = this.document.toJSON();
      data.document.content = this.document.content.toXml();
      data.element_id = this.xmlElement.getAttribute('eId');

      if (!data.element_id && this.xmlElement.tagName !== "akomaNtoso") {
        // for elements without ids (preamble, preface, components)
        data.element_id = this.xmlElement.tagName;
      }

      $.ajax({
        url: '/api/documents/' + this.comparisonDocumentId + '/diff',
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"})
          .then(function(response) {
            var html = $.parseHTML(response.html_diff)[0];

            self.makeLinksExternal(html);
            self.addWorkPopups(html);
            self.makeTablesEditable(html);
            self.makeElementsQuickEditable(html);
            self.highlightQuickEditElement(html);
            self.aknElement.classList.add('diffset');
            self.aknElement.replaceChildren(html);

            self.trigger('rendered');
          });
    },

    renderCoverpage: function() {
      // Render a coverpage and return it via a deferred.
      // Uses a cached coverpage, if available.
      var deferred = $.Deferred(),
          self = this;

      if (this.coverpageCache) {
        deferred.resolve(this.coverpageCache);
      } else {
        var data = JSON.stringify({'document': self.document.toJSON()});
        $.ajax({
          url: this.document.url() + '/render/coverpage',
          type: "POST",
          data: data,
          contentType: "application/json; charset=utf-8",
          dataType: "json"})
          .then(function(response) {
            var html = $.parseHTML(response.output);
            self.coverpageCache = html;
            deferred.resolve(html);
          });
      }

      return deferred;
    },

    makeLinksExternal: function(html) {
      html.querySelectorAll('a[href]').forEach(function(a) {
        if (!a.getAttribute('href').startsWith('#')) {
          a.setAttribute("target", "_blank");
          $(a).tooltip({title: a.getAttribute('data-href') || a.getAttribute('href')});
        }
      });
    },

    addWorkPopups: function(html) {
      html.querySelectorAll('a[href^="/works/"]').forEach(function(a) {
        a.setAttribute("data-popup-url", a.href + '/popup');
        $(a).tooltip('disable');
      });
    },

    makeTablesEditable: function(html) {
      var tables = html.querySelectorAll('table[id]'),
          self = this;

      tables.forEach(function(table) {
        var w = self.tableEditor.tableWrapper.cloneNode(true),
            $w = $(w);

        $w.find('button').data('table-id', table.id);
        table.insertAdjacentElement('beforebegin', w);
        // we bind the CKEditor instance to this div, since CKEditor can't be
        // directly attached to the table element
        $w.find('.table-container').append(table);
      });
    },

    makeElementsQuickEditable: function(html) {
      var self = this;

      $(html)
        .find(this.document.tradition().settings.grammar.quickEditable)
        .addClass('quick-editable')
        .each(function(i, e) {
          self.ensureGutterActions(e).append(self.quickEditTemplate.cloneNode(true));
        });
    },

    highlightQuickEditElement: function(html) {
      if (this.aknTextEditor.editing && this.aknTextEditor.xmlElement !== this.xmlElement) {
        const eid = this.aknTextEditor.xmlElement.getAttribute('eId');
        if (eid) {
          const el = html.querySelector('[id="' + eid + '"]');
          if (el) {
            el.classList.add('quick-editing');
          }
        }
      }
    },

    // Ensure this element has a gutter actions child
    ensureGutterActions: function(elem) {
      if (!elem.firstElementChild || !elem.firstElementChild.classList.contains('gutter-actions')) {
        var div = document.createElement('div');
        div.className = 'gutter-actions ig';
        elem.prepend(div);
      }

      return elem.firstElementChild;
    },

    editTable: function(e) {
      var tableId = $(e.currentTarget).data('table-id');

      if (this.confirmAndDiscardChanges()) {
        // we queue this up to run after the click event has finished, because we need the HTML to be re-rendered
        // after changes are potentially discarded
        setTimeout(() => {
          const table = document.getElementById(tableId);

          if (!this.tableEditor.canEditTable(table)) {
            alert($t('This table contains content that cannot be edited in this mode. Edit the table in text mode instead.'));
          } else {
            this.editActivityStarted('table');
            this.tableEditor.editTable(table);
            // disable other table edit buttons
            this.$('.edit-table').prop('disabled', true);
          }
        }, 0);
      }
    },

    onTableEditStart: function() {
      this.toolbar.classList.add('is-editing', 'edit-mode-table');
    },

    onTableEditFinish: function() {
      // enable all table edit buttons
      this.$('.edit-table').prop('disabled', false);
      this.toolbar.classList.remove('is-editing', 'edit-mode-table');
    },

    toggleShowStructure: function(e) {
      const show = e.currentTarget.classList.toggle('active');
      this.el.querySelector('#document-sheet la-akoma-ntoso').classList.toggle('show-structure', show);
    },

    toggleShowComparison: function(e) {
      const show = !e.currentTarget.classList.contains('active');
      const menuItem = e.currentTarget.parentElement.previousElementSibling;

      $(e.currentTarget).siblings().removeClass('active');
      this.setComparisonDocumentId(show ? e.currentTarget.getAttribute('data-id') : null);
      e.currentTarget.classList.toggle('active');

      menuItem.classList.toggle('btn-outline-secondary', !show);
      menuItem.classList.toggle('btn-primary', show);
    },

    refPopup: function (e) {
      const element = e.target;
      const href = element.getAttribute('href');
      if (!href || !href.startsWith('#')) return;
      const eId = href.substring(1);

      if (element._tippy) return;

      const target = this.document.content.xpath(
        `//a:*[@eId="${eId}"]`, undefined, XPathResult.FIRST_ORDERED_NODE_TYPE).singleNodeValue;

      if (target) {
        // render
        const html = document.createElement('la-akoma-ntoso');
        html.appendChild(this.htmlRenderer.renderXmlElement(this.document, target));

        tippy(element, {
          content: html.outerHTML,
          allowHTML: true,
          interactive: true,
          theme: 'light',
          placement: 'bottom-start',
          appendTo: document.getElementById("document-sheet"),
        });
      }
    },

    toggleTextEditor: function (visible) {
      document.querySelector('#document-primary-pane-splitter').classList.toggle('d-none', !visible);
      document.querySelector('.document-primary-pane-editor-pane').classList.toggle('d-none', !visible);
    },

    isDirty: function () {
      return this.aknTextEditor.dirty || this.tableEditor.editing;
    }
  });
})(window);
