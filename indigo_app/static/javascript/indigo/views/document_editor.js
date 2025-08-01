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
      this.quickEditEid = null;
      this.quickEditTemplate = $('<a href="#" class="quick-edit"><i class="fas fa-pencil-alt"></i></a>')[0];
      this.contentPane = document.querySelector('.document-primary-pane-content-pane');
      this.sheetInner = this.contentPane.querySelector('.document-workspace .document-sheet-container .sheet-inner');
      this.aknElement = this.contentPane.querySelector('la-akoma-ntoso');
      this.toolbar = document.querySelector('.document-toolbar-wrapper');

      this.aknTextEditor = new Indigo.AknTextEditor(
        this.el.querySelector('.document-primary-pane-editor-pane'),
        this.document,
        this.onTextEditSaved.bind(this),
        this.onTextEditCancelled.bind(this),
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
      this.tableEditor.on('finish', this.onTableEditFinish, this);
      this.tableEditor.on('discard', this.editActivityCancelled, this);
      this.tableEditor.on('save', this.editActivityEnded, this);

      // setup renderer
      this.editorReady = $.Deferred();
      this.setupRenderers();

      // fake a click on the previous point in time for comparison, if there is one
      let defaultCompareTo = document.querySelector('.show-pit-comparison.default-compare-to');
      if (defaultCompareTo) {
        defaultCompareTo.click();
      }
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
      this.quickEditEid = null;
      this.editXmlElement(this.xmlElement);
    },

    quickEdit: function(e) {
      if (this.confirmAndDiscardChanges()) {
        const htmlElement = e.currentTarget.parentElement.parentElement;
        this.quickEditEid = htmlElement.id;
        const element = this.document.content.xmlDocument.querySelector('[eId="' + this.quickEditEid + '"]');
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
        document.body.classList.add('is-editing', 'edit-mode-text');
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
     * Discard the content of all editors.
     */
    discardChanges: function() {
      this.tableEditor.discardChanges(true);
      this.aknTextEditor.discardChanges();
    },

    closeTextEditor: function(e) {
      this.toggleTextEditor(false);
      this.aknElement.querySelector('.quick-editing')?.classList.remove('quick-editing');
      document.body.classList.remove('is-editing', 'edit-mode-text');
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
     * @param mutations an array of MutationRecord objects
     */
    onDomMutated: function(model, mutations) {
      // process each mutation in order; we stop processing after finding the first one that significantly impacts us
      for (const mutation of mutations) {
        let eid = mutation.target.getAttribute ? mutation.target.getAttribute('eId') : null;

        switch (model.getMutationImpact(mutation, this.xmlElement)) {
          case 'replaced':
            this.xmlElement = mutation.addedNodes[0];
            this.render();
            return;
          case 'changed':
            if (this.quickEditEid && eid !== this.quickEditEid) {
              // Check for the special case of the quick-edited element being replaced, so that we can re-render
              // just that element (if possible). In this case the mutation target is the parent and its children have
              // changed.

              if (mutation.type === 'childList' && mutation.removedNodes.length === 1 &&
                mutation.removedNodes[0]?.getAttribute('eId') === this.quickEditEid) {
                // the quick-edited element was removed or replaced

                if (mutation.addedNodes.length === 1) {
                  if (mutation.addedNodes[0]?.getAttribute('eId') === this.quickEditEid) {
                    // it was replaced but retained the eid
                    eid = this.quickEditEid;
                  } else {
                    // it was replaced with a different eid; re-render the target but track the new eid
                    this.quickEditEid = mutation.addedNodes[0].getAttribute('eId');
                  }
                } else {
                  // it was removed
                  this.quickEditEid = null;
                }
              }
            }

            // eid can be null, in which case everything is re-rendered
            this.render(eid);
            return;
          case 'removed':
            // the change removed xmlElement from the tree
            console.log('Mutation removes SourceEditor.xmlElement from the tree');
            this.discardChanges();
            return;
        }
      }
    },

    onTextEditSaved: function() {
      this.editActivityEnded();
      this.closeTextEditor();
    },

    onTextEditCancelled: function() {
      this.editActivityCancelled();
      this.closeTextEditor();
    },

    editActivityStarted: function(mode) {
      this.trigger('edit-activity-started', mode);
    },

    editActivityEnded: function() {
      this.trigger('edit-activity-ended');
    },

    editActivityCancelled: function() {
      this.trigger('edit-activity-cancelled');
    },

    /**
     * Render the XML element into HTML, add quick edit buttons, make links external, etc.
     * @param eid only re-render a specific element, if possible. The element must be in the old and new trees.
     */
    render: async function(eid) {
      if (!this.xmlElement) return;

      this.sheetInner.classList.toggle('is-fragment', this.xmlElement.parentElement !== null);

      // what xml element must be rendered, and where must it be placed into the tree?
      let toRender, oldElement;
      if (eid && this.xmlElement.getAttribute('eId') !== eid) {
        // we're rendering a child element; try to find the old element to replace
        // if the new element has a changed eId, then we may not be able to find the old element, in which case
        // we'll just re-render everything
        toRender = this.xmlElement.querySelector('[eId="' + eid + '"]');
        oldElement = this.aknElement.querySelector('[data-eid="' + eid + '"]');
      }

      if (!toRender || !oldElement) {
        // if we can't find the element or where to put it, just render everything
        toRender = this.xmlElement;
        oldElement = null;
      }

      // ensure the renderer is ready
      await Indigo.deferredToAsync(this.htmlRenderer.ready);

      const html = this.htmlRenderer.renderXmlElement(this.document, toRender);
      this.prepareHtmlForRender(html);

      if (oldElement) {
        oldElement.replaceWith(html);
      } else {
        this.aknElement.replaceChildren(html);
      }

      // render the coverpage asynchronously
      if (!eid && this.xmlElement.parentElement === null && Indigo.Preloads.provisionEid === "") {
        const coverpage = document.createElement('div');
        coverpage.className = 'spinner-when-empty';
        this.aknElement.insertAdjacentElement('afterbegin', coverpage);
        this.renderCoverpage().then((nodes) => {
          if (nodes) {
            for (const node of nodes) {
              coverpage.append(node);
            }
          }
        });
      }

      this.trigger('rendered');
      this.renderComparisonDiff();
    },

    renderComparisonDiff: function() {
      let self = this;

      if (!this.comparisonDocumentId) return;

      const data = this.document.content.toSimplifiedJSON();
      // slight difference to provision_eid -- doesn't treat the document XML as a portion
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

            self.prepareHtmlForRender(html);
            self.aknElement.classList.add('diffset');
            self.aknElement.replaceChildren(html);
            self.trigger('rendered');
          });
    },

    prepareHtmlForRender: function(html) {
      this.makeLinksExternal(html);
      this.addWorkPopups(html);
      this.tableEditor.makeTablesEditable(html);
      this.makeElementsQuickEditable(html);
      this.highlightQuickEditElement(html);
    },

    renderCoverpage: async function() {
      if (!this.coverpageCache) {
        const data = JSON.stringify({'document': this.document.toJSON()});
        const resp = await fetch(this.document.url() + '/render/coverpage', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json; charset=utf-8',
            'X-CSRFToken': Indigo.csrfToken,
          },
          body: data,
        });
        if (resp.ok) {
          this.coverpageCache = $.parseHTML((await resp.json())['output']);
        }
      }
      return this.coverpageCache;
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
      const tableId = e.currentTarget.dataset.tableId;

      if (this.confirmAndDiscardChanges()) {
        // ensure the text editor is closed, even if there were no changes
        this.aknTextEditor.discardChanges();

        // we queue this up to run after the click event has finished, because we need the HTML to be re-rendered
        // after changes are potentially discarded
        setTimeout(() => {
          const table = document.getElementById(tableId);

          if (!this.tableEditor.canEditTable(table)) {
            alert($t('This table contains content that cannot be edited in this mode. Edit the table in text mode instead.'));
          } else {
            this.editActivityStarted('table');
            document.body.classList.add('is-editing', 'edit-mode-table');
            this.tableEditor.editTable(table);
          }
        }, 0);
      }
    },

    onTableEditFinish: function() {
      document.body.classList.remove('is-editing', 'edit-mode-table');
    },

    toggleShowStructure: function(e) {
      const show = e.currentTarget.classList.toggle('active');
      this.aknElement.classList.toggle('show-structure', show);
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
