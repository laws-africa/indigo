(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * The SourceEditorView manages rendering and editing (via text, xml or table editors) of an xml element. It handles
   * moving between the different editors and updates the document model when changes are made.
   *
   * It can have two active xml elements, which are only different in quick edit mode:
   *
   * - the one being rendered (xmlElement)
   * - the one being edited (editingXmlElement)
   */
  Indigo.SourceEditorView = Backbone.View.extend({
    el: 'body',
    events: {
      // TODO: remove these two?
      'click .text-editor-buttons .btn.save': 'saveTextEditor',
      'click .text-editor-buttons .btn.cancel': 'onCancelClick',
      'click .show-structure': 'toggleShowStructure',
      'click .show-pit-comparison': 'toggleShowComparison',
      'click .edit-table': 'editTable',
      'click .quick-edit': 'quickEdit',
      'mouseenter la-akoma-ntoso .akn-ref[href^="#"]': 'refPopup',
    },

    initialize: function(options) {
      this.parent = options.parent;
      this.name = 'source';
      // flag to prevent circular updates
      this.updating = false;
      this.document = this.parent.model;
      // the element currently being shown
      this.xmlElement = null;
      // the element currently being edited -- can be different to the above during quick edit
      this.editingXmlElement = null;
      this.quickEditTemplate = $('<a href="#" class="quick-edit"><i class="fas fa-pencil-alt"></i></a>')[0];

      this.aknTextEditor = new Indigo.AknTextEditor(
        this.el,
        this.document,
        this.onTextElementParsed.bind(this),
      );

      this.xmlEditor = new Indigo.XMLEditor(
        document.querySelector('.document-xml-editor'),
        this.document,
        this.onXmlElementParsed.bind(this),
      );

      // setup renderer
      this.editorReady = $.Deferred();
      this.listenTo(this.document, 'change', this.onDocumentChanged);

      // setup table editor
      this.tableEditor = new Indigo.TableEditorView({parent: this, documentContent: this.parent.documentContent});
      this.tableEditor.on('start', this.tableEditStart, this);
      this.tableEditor.on('finish', this.tableEditFinish, this);
      this.tableEditor.on('discard', this.editActivityCancelled, this);
      this.tableEditor.on('save', this.editActivityEnded, this);

      this.$toolbar = $('.document-editor-toolbar');

      this.setupRenderers();
    },

    setupRenderers: function() {
      var country = this.document.get('country'),
          self = this;

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

    quickEdit: function(e) {
      var elemId = e.currentTarget.parentElement.parentElement.id,
          element = this.parent.documentContent.xmlDocument;

      // the id might be scoped
      elemId.split("/").forEach(function(id) {
        element = element.querySelector('[eId="' + id + '"]');
      });

      if (element) this.editXmlElement(element);
    },

    /**
     * Edit the given XML element in the text editor.
     */
    editXmlElement: function(element) {
      this.editingXmlElement = element;
      this.aknTextEditor.setXmlElement(element);
      this.xmlEditor.setXmlElement(element);

      // if we're not already editing, activate the editor
      if (!this.updating) {
        this.editActivityStarted('text');
        this.aknTextEditor.monacoEditor.focus();
      }
    },

    saveTextEditor: function(e) {
      this.editActivityEnded();
      var self = this;
      var $btn = this.$('.text-editor-buttons .btn.save');
      var content = this.monacoEditor.getValue();
      var fragmentRule = this.document.tradition().grammarRule(this.editingXmlElement);

      // should we delete the item?
      if (!content.trim() && fragmentRule !== 'akomaNtoso') {
        if (confirm($t('Go ahead and delete this section from the document?'))) {
          this.parent.removeFragment(this.editingXmlElement);
        }
        return;
      }

      // TODO: all this falls away

      $btn
        .attr('disabled', true)
        .find('.fa')
          .removeClass('fa-check')
          .addClass('fa-spinner fa-pulse');

      // The actual response to update the view is done
      // in a deferred so that we can cancel it if the
      // user clicks 'cancel'
      var deferred = this.pendingTextSave = $.Deferred();
      deferred
        .then(function(response) {
          var newFragment = $.parseXML(response.output);

          if (fragmentRule === 'akomaNtoso') {
            // entire document
            newFragment = [newFragment.documentElement];
          } else {
            newFragment = newFragment.documentElement.children;
          }

          this.updating = true;
          try {
            self.parent.updateFragment(self.editingXmlElement, newFragment);
          } finally {
            this.updating = false;
          }
        })
        .fail(function(xhr, status, error) {
          // this will be null if we've been cancelled without an ajax response
          if (xhr) {
            if (xhr.status === 400) {
              Indigo.errorView.show(xhr.responseJSON.content || error || status);
            } else {
              Indigo.errorView.show(error || status);
            }
          }
        })
        .always(function() {
          // TODO: this doesn't feel like it's in the right place;
          $btn
            .attr('disabled', false)
            .find('.fa')
              .removeClass('fa-spinner fa-pulse')
              .addClass('fa-check');
        });

      var id = this.editingXmlElement.getAttribute('eId'),
          data = {
        'content': content,
      };
      if (fragmentRule !== 'akomaNtoso') {
        data.fragment = fragmentRule;
        if (id && id.lastIndexOf('__') > -1) {
          // retain the id of the parent element as the prefix
          data.id_prefix = id.substring(0, id.lastIndexOf('__'));
        }
      }

      $.ajax({
        url: this.document.url() + '/parse',
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"})
        .done(function(response) {
          deferred.resolve(response);
        })
        .fail(function(xhr, status, error) {
          deferred.reject(xhr, status, error);
        });
    },

    /**
     * Set the XML element that is currently being shown.
     *
     * This may be called when the XML editor or the text editor provide an updated element to edit, in which case
     * this.updating will be true.
     */
    showXmlElement: function(element) {
      // show node, a node in the XML document
      if (!this.updating) {
        this.tableEditor.discardChanges(null, true);
      }

      this.xmlElement = element;
      this.render();
      this.editXmlElement(element);

      if (!this.updating) {
        this.$('.document-sheet-container').scrollTop(0);
      }
    },

    /** There is newly parsed XML from the akn text editor */
    onTextElementParsed: function(elements) {
      this.updating = true;
      try {
        this.parent.updateFragment(this.editingXmlElement, elements);
      } finally {
        this.updating = false;
      }
    },

    /**
     * The XML editor has parsed its XML into a new element.
     */
    onXmlElementParsed: function(element) {
      this.updating = true;
      try {
        this.parent.updateFragment(this.editingXmlElement, [element]);
      } finally {
        this.updating = false;
      }
    },

    onCancelClick() {
      this.editActivityCancelled();
    },

    onDocumentChanged: function() {
      this.coverpageCache = null;
      this.render();
    },

    editActivityStarted: function(mode) {
    },

    editActivityEnded: function() {
    },

    editActivityCancelled: function() {
    },

    // Save the content of the editor into the DOM, returns a Deferred
    saveChanges: function() {
      this.tableEditor.saveChanges();
      return $.Deferred().resolve();
    },

    // Discard the content of the editor, returns a Deferred
    discardChanges: function() {
      this.tableEditor.discardChanges(null, true);
      return $.Deferred().resolve();
    },

    render: function() {
      if (!this.xmlElement) return;

      var self = this,
          renderCoverpage = this.xmlElement.parentElement === null,
          $akn = this.$('.document-workspace-content la-akoma-ntoso'),
          coverpage;

      $akn[0].classList.add('spinner-when-empty');
      $akn.empty();

      if (renderCoverpage) {
        coverpage = document.createElement('div');
        coverpage.className = 'spinner-when-empty';
        $akn.append(coverpage);
        this.renderCoverpage().then(function(node) {
          $(coverpage).append(node);
          self.trigger('rendered');
        });
      }

      this.htmlRenderer.ready.then(function() {
        var html = self.htmlRenderer.renderXmlElement(self.document, self.xmlElement);

        self.makeLinksExternal(html);
        self.addWorkPopups(html);
        self.makeTablesEditable(html);
        self.makeElementsQuickEditable(html);
        $akn.append(html);

        self.trigger('rendered');
        self.renderComparisonDiff();
      });
    },

    renderComparisonDiff: function() {
      var self = this,
          $akn = this.$('.document-workspace-content la-akoma-ntoso'),
          data = {};

      if (!this.comparisonDocumentId) return;

      data.document = this.document.toJSON();
      data.document.content = this.parent.documentContent.toXml();
      data.element_id = this.xmlElement.getAttribute('eId');

      if (!data.element_id && this.xmlElement.tagName !== "akomaNtoso") {
        // for elements without ids (preamble, preface, components)
        data.element_id = this.xmlElementxmlElement.tagName;
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
            $akn.empty();
            $akn.addClass('diffset');
            $akn.append(html);

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
      this.editActivityStarted('table');
      var $btn = $(e.currentTarget),
          table = document.getElementById($btn.data('table-id'));

      if (!this.tableEditor.canEditTable(table)) {
        alert($t('This table contains content that cannot be edited in this mode. Edit the table in text mode instead.'));
      } else {
        this.tableEditor.editTable(table);
        // disable other table edit buttons
        this.$('.edit-table').prop('disabled', true);
      }
    },

    tableEditStart: function() {
      this.$('.edit-text').hide();

      // adjust the toolbar
      // TODO
      this.$toolbar.find('.btn-toolbar').addClass('d-none');
      this.$('.document-workspace-buttons').addClass('d-none');
    },

    tableEditFinish: function() {
      this.$('.edit-text').show();
      // enable all table edit buttons
      this.$('.edit-table').prop('disabled', false);

      // adjust the toolbar
      // TODO
      this.$toolbar.find('.btn-toolbar').addClass('d-none');
      this.$toolbar.find('.general-buttons').removeClass('d-none');
      this.$('.document-workspace-buttons').removeClass('d-none');
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

    resize: function() {},
  });

  // Handle the document editor, tracking changes and saving it back to the server.
  Indigo.DocumentEditorView = Backbone.View.extend({
    el: 'body',

    initialize: function(options) {
      this.dirty = false;

      this.documentContent = options.documentContent;
      // XXX: check
      this.documentContent.on('change', this.setDirty, this);
      this.documentContent.on('sync', this.setClean, this);

      this.tocView = options.tocView;
      this.tocView.selection.on('change', this.tocSelectionChanged, this);

      // setup the editor views
      this.sourceEditor = new Indigo.SourceEditorView({parent: this});

      // this is a deferred to indicate when the editor is ready to edit
      this.editorReady = this.sourceEditor.editorReady;
      this.editorReady.then(() => {
        this.editFragment(this.documentContent.xmlDocument.documentElement);
      });
    },

    tocSelectionChanged: function(selection) {
      var self = this;

      this.stopEditing()
        .then(function() {
          if (selection) {
            self.editFragment(selection.get('element'));
          }
        });
    },

    stopEditing: function() {
      return this.sourceEditor.discardChanges();
    },

    editFragment: function(fragment) {
      if (!this.updating && fragment) {
        console.log("Editing new fragment");

        var isRoot = fragment.parentElement === null;

        this.fragment = fragment;
        this.$('.document-content-view .document-sheet-container .sheet-inner').toggleClass('is-fragment', !isRoot);

        this.sourceEditor.showXmlElement(fragment);
      }
    },

    removeFragment: function(fragment) {
      fragment = fragment || this.fragment;
      this.documentContent.replaceNode(fragment, null);
    },

    updateFragment: function(oldNode, newNodes) {
      this.updating = true;
      try {
        var updated = this.documentContent.replaceNode(oldNode, newNodes);
        if (oldNode === this.fragment) {
          this.fragment = updated;
          this.sourceEditor.showXmlElement(updated);
        }
        // TODO: need to set the element?
        this.sourceEditor.render();
      } finally {
        this.updating = false;
      }
    },

    setDirty: function() {
      if (!this.dirty) {
        this.dirty = true;
        this.trigger('dirty');
      }
    },

    setClean: function() {
      if (this.dirty) {
        this.dirty = false;
        this.trigger('clean');
      }
    },

    isDirty: function() {
      return this.dirty;
    },

    canCancelEdits: function() {
      return (!this.isDirty() || confirm($t("You will lose your changes, are you sure?")));
    },

    // Save the content of the editor, returns a Deferred
    save: function() {
      var self = this,
          deferred = $.Deferred();

      function ok() { deferred.resolve(); }
      function fail() { deferred.reject(); }

      if (!this.dirty) {
        // don't do anything if it hasn't changed
        ok();

      } else {
          // ask the editor to returns its contents
        this.sourceEditor
          .saveChanges()
          .done(function() {
            // save the model
            self.saveModel().done(ok).fail(fail);
          })
          .fail(fail);
      }

      return deferred;
    },

    // Save the content of the document, returns a Deferred
    saveModel: function() {
      return this.documentContent.save();
    },

  });
})(window);
