(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // The SourceEditorView manages the interaction between
  // the model, the wrapping document editor view, and the source (xml) and
  // text editor components.
  Indigo.SourceEditorView = Backbone.View.extend({
    el: 'body',
    events: {
      'click .text-editor-buttons .btn.save': 'saveTextEditor',
      'click .text-editor-buttons .btn.cancel': 'closeTextEditor',
      'click .btn.edit-text': 'fullEdit',
      'click .btn.edit-table': 'editTable',
      'click .quick-edit': 'quickEdit',

      'click .editor-action': 'triggerEditorAction',

      'click .insert-image': 'insertImage',
      'click .insert-remark': 'insertRemark',
    },

    initialize: function(options) {
      this.parent = options.parent;
      this.name = 'source';
      this.editing = false;
      this.updating = false;
      this.quickEditTemplate = $('<a href="#" class="quick-edit"><i class="fas fa-pencil-alt"></i></a>')[0];

      this.grammarName = this.parent.model.tradition().settings.grammar.name;
      this.grammarModel = new Indigo.grammars.registry[this.grammarName](
        this.parent.model.get('frbr_uri'),
        this.parent.model.url() + '/static/xsl/text.xsl');
      this.grammarModel.setup();

      // setup renderer
      this.editorReady = $.Deferred();
      this.listenTo(this.parent.model, 'change', this.documentChanged);

      this.$textEditor = this.$('.document-text-editor');

      // setup table editor
      this.tableEditor = new Indigo.TableEditorView({parent: this, documentContent: this.parent.documentContent});
      this.tableEditor.on('start', this.tableEditStart, this);
      this.tableEditor.on('finish', this.tableEditFinish, this);

      this.$toolbar = $('.document-editor-toolbar');

      this.setupRenderers();

      // get the appropriate remark style for the tradition
      this.remarkGenerator = Indigo.remarks[this.parent.model.tradition().settings.remarkGenerator];

      this.initLinters();
    },

    initLinters: function() {
      debugger;
      var Indigo = exports.Indigo,
          defaults = Indigo.traditions.default.settings;

      // Adjust the base definition to include articles
      defaults.grammar.fragments.article = 'articles';
      defaults.grammar.fragments.quickEditable = '.akn-chapter, .akn-part, .akn-section, .akn-article, .akn-component, .akn-components';
      defaults.toc.elements.article = 1;
      defaults.toc.titles.article = function(i) {
        return "Art. " + i.num + (i.heading ? " – " + i.heading : '');
      };
      // default remark generator
      defaults.remarkGenerator = 'laTraditionGenerator';

      // linters to be run by default - we push values so that grammars that have inherited these defaults
      // pick them up
      defaults.linters.push('upperCaseHeadings');
      defaults.linters.push('onlySchedule');
      defaults.linters.push('duplicateSections');
      defaults.linters.push('duplicateElements');
      defaults.linters.push('suspiciouslyNumberedItems');
      defaults.linters.push('nonSequentialSections');
      defaults.linters.push('numberedElementsSequentialAndOnlyOne');
      defaults.linters.push('emptySections');
      defaults.linters.push('spaceBeforePunctuation');
      defaults.linters.push('spaceMissingAfterPunctuation');
      defaults.linters.push('metreSquared');
      defaults.linters.push('missingImageAttachments');
      defaults.linters.push('hrefContainsSpace');
      defaults.linters.push('hrefEndsWithStop');
      defaults.linters.push('hrefMissingProtocol');
      defaults.linters.push('hyphenSpace');

      /**
       * Extend Slaw grammar model to add additional syntax highlighting.
       */
      class SlawLAGrammarModel extends Indigo.grammars.registry.slaw {
        constructor(...args) {
          super(...args);
          this.language_def.hier = /Part|Chapter|Subpart|Article|PARA/i;
        }
      }

      Indigo.grammars.registry.slaw = SlawLAGrammarModel;

      let bluebell_settings = {
        country: null,
        toc: {
          elements: {
            akomaNtoso: 1,
            article: 1,
            attachment: 1,
            attachments: 1,
            chapter: 1,
            conclusions: 1,
            coverpage: 1,
            division: 1,
            paragraph: 1,
            part: 1,
            preamble: 1,
            preface: 1,
            section: 1,
            subdivision: 1,
            subpart: 1,
          },
        },
        grammar: {
          name: 'bluebell',
          fragments: {
            article: 'hier_element_block',
            attachment: 'attachment',
            attachments: 'attachments',
            chapter: 'hier_element_block',
            division: 'hier_element_block',
            paragraph: 'hier_element_block',
            part: 'hier_element_block',
            section: 'hier_element_block',
            subdivision: 'hier_element_block',
            subpart: 'hier_element_block',
          },
          quickEditable: '.akn-article, .akn-attachment, .akn-chapter, .akn-division, .akn-paragraph, .akn-part, .akn-section, .akn-subdivision, .akn-subpart',
        },
      }

      let bluebell_settings_aa = bluebell_settings;
      bluebell_settings_aa.country = 'aa';
      Indigo.traditions.aa = new Indigo.Tradition(bluebell_settings_aa);

      let bluebell_settings_un = bluebell_settings;
      bluebell_settings_un.country = 'un';
      Indigo.traditions.un = new Indigo.Tradition(bluebell_settings_un);

      let bluebell_settings_xx = bluebell_settings;
      bluebell_settings_xx.country = 'xx';
      Indigo.traditions.xx = new Indigo.Tradition(bluebell_settings_xx);
    },

    setupTextEditor: function() {
      if (!this.textEditor) {
        this.textEditor = window.monaco.editor.create(
          this.el.querySelector('.document-text-editor .monaco-editor'),
          this.grammarModel.monacoOptions()
        );
        new ResizeObserver(() => { this.textEditor.layout(); }).observe(this.textEditor.getContainerDomNode());
        this.grammarModel.setupEditor(this.textEditor);
      }
    },

    documentChanged: function() {
      this.coverpageCache = null;
      this.render();
    },

    setupRenderers: function() {
      var country = this.parent.model.get('country'),
          self = this;

      // setup akn to html transform
      this.htmlRenderer = Indigo.render.getHtmlRenderer(this.parent.model);
      this.htmlRenderer.ready.then(function() {
        self.editorReady.resolve();
      });

      // setup akn to text transform
      this.textTransformReady = $.Deferred();
      $.get(this.parent.model.url() + '/static/xsl/text.xsl').then(function(xml) {
        var textTransform = new XSLTProcessor();
        textTransform.importStylesheet(xml);

        self.textTransform = textTransform;
        self.textTransformReady.resolve();
      });
    },

    setComparisonDocumentId: function(id) {
      this.comparisonDocumentId = id;
      this.render();
    },

    fullEdit: function(e) {
      e.preventDefault();
      this.editFragmentText(this.parent.fragment);
    },

    quickEdit: function(e) {
      var elemId = e.currentTarget.parentElement.parentElement.id,
          node = this.parent.documentContent.xmlDocument;

      // the id might be scoped
      elemId.split("/").forEach(function(id) {
        node = node.querySelector('[eId="' + id + '"]');
      });

      if (node) this.editFragmentText(node);
    },

    editFragmentText: function(fragment) {
      var self = this;

      this.editing = true;
      this.fragment = fragment;

      // ensure source code is hidden
      this.$('.btn.show-xml-editor.active').click();

      // show the edit toolbar
      this.$toolbar.find('.btn-toolbar').addClass('d-none');
      this.$toolbar.find('.text-editor-buttons').removeClass('d-none');
      this.$('.document-workspace-buttons').addClass('d-none');

      // text from node in the actual XML document
      const text = this.grammarModel.xmlToText(this.fragment);

      // show the text editor
      this.$('.document-content-view').addClass('show-text-editor');

      this.setupTextEditor();
      this.textEditor.setValue(text);
      this.textEditor.layout();
      const top = {column: 1, lineNumber: 1};
      this.textEditor.setPosition(top);
      this.textEditor.revealPosition(top);
      this.textEditor.focus();

      this.$textEditor
        .data('fragment', this.fragment.tagName)
        .show();

      this.$('.document-sheet-container').scrollTop(0);
    },

    saveTextEditor: function(e) {
      var self = this;
      var $btn = this.$('.text-editor-buttons .btn.save');
      var content = this.textEditor.getValue();
      var fragmentRule = this.parent.model.tradition().grammarRule(this.fragment);

      // should we delete the item?
      if (!content.trim() && fragmentRule != 'akomaNtoso') {
        if (confirm('Go ahead and delete this section from the document?')) {
          this.parent.removeFragment(this.fragment);
        }
        return;
      }

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
            self.parent.updateFragment(self.fragment, newFragment);
          } finally {
            this.updating = false;
          }
          self.closeTextEditor();
        })
        .fail(function(xhr, status, error) {
          // this will be null if we've been cancelled without an ajax response
          if (xhr) {
            if (xhr.status == 400) {
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

      var id = this.fragment.getAttribute('eId'),
          data = {
        'content': content,
      };
      if (fragmentRule != 'akomaNtoso') {
        data.fragment = fragmentRule;
        if (id && id.lastIndexOf('__') > -1) {
          // retain the id of the parent element as the prefix
          data.id_prefix = id.substring(0, id.lastIndexOf('__'));
        }
      }

      $.ajax({
        url: this.parent.model.url() + '/parse',
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

    closeTextEditor: function(e) {
      if (this.pendingTextSave) {
        this.pendingTextSave.reject();
        this.pendingTextSave = null;
      }

      this.$('.document-content-view').removeClass('show-text-editor');

      // adjust the toolbar
      this.$toolbar.find('.btn-toolbar').addClass('d-none');
      this.$toolbar.find('.general-buttons').removeClass('d-none');
      this.$('.document-workspace-buttons').removeClass('d-none');

      this.editing = false;
    },

    editFragment: function(node) {
      // edit node, a node in the XML document
      if (!this.updating) {
        this.tableEditor.discardChanges(null, true);
        this.closeTextEditor();
        this.render();
        this.$('.document-sheet-container').scrollTop(0);
      }
    },

    // Save the content of the editor into the DOM, returns a Deferred
    saveChanges: function() {
      this.tableEditor.saveChanges();
      this.closeTextEditor();
      return $.Deferred().resolve();
    },

    // Discard the content of the editor, returns a Deferred
    discardChanges: function() {
      this.tableEditor.discardChanges(null, true);
      this.closeTextEditor();
      return $.Deferred().resolve();
    },

    render: function() {
      if (!this.parent.fragment) return;

      var self = this,
          renderCoverpage = this.parent.fragment.parentElement === null,
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
        });
      }

      this.htmlRenderer.ready.then(function() {
        var html = self.htmlRenderer.renderXmlElement(self.parent.model, self.parent.fragment);

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

      data.document = this.parent.model.toJSON();
      data.document.content = this.parent.documentContent.toXml();
      data.element_id = this.parent.fragment.getAttribute('eId');

      if (!data.element_id && this.parent.fragment.tagName !== "akomaNtoso") {
        // for elements without ids (preamble, preface, components)
        data.element_id = this.parent.fragment.tagName;
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
        var data = JSON.stringify({'document': self.parent.model.toJSON()});
        $.ajax({
          url: this.parent.model.url() + '/render/coverpage',
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
        .find(this.parent.model.tradition().settings.grammar.quickEditable)
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
      var $btn = $(e.currentTarget),
          table = document.getElementById($btn.data('table-id'));
      this.tableEditor.editTable(table);
      // disable other table edit buttons
      this.$('.edit-table').prop('disabled', true);
    },

    tableEditStart: function() {
      this.$('.edit-text').hide();

      // adjust the toolbar
      this.$toolbar.find('.btn-toolbar').addClass('d-none');
      this.$('.document-workspace-buttons').addClass('d-none');

      this.editing = true;
    },

    tableEditFinish: function() {
      this.$('.edit-text').show();
      // enable all table edit buttons
      this.$('.edit-table').prop('disabled', false);

      // adjust the toolbar
      this.$toolbar.find('.btn-toolbar').addClass('d-none');
      this.$toolbar.find('.general-buttons').removeClass('d-none');
      this.$('.document-workspace-buttons').removeClass('d-none');

      this.editing = false;
    },

    triggerEditorAction: function(e) {
      // an editor action from the toolbar
      e.preventDefault();
      const action = e.target.getAttribute('data-action');
      this.textEditor.trigger('indigo', action);
      this.textEditor.focus();
    },

    /**
     * Setup the box to insert an image into the document text.
     */
    insertImage: function(e) {
      var self = this;

      e.preventDefault();

      if (!this.insertImageBox) {
        // setup insert-image box
        this.insertImageBox = new Indigo.InsertImageView({document: this.parent.model});
      }

      let image = this.grammarModel.getImageAtCursor(this.textEditor);
      let selected = null;

      if (image) {
        let filename = image.src;
        if (filename.startsWith("media/")) filename = filename.substr(6);
        selected = this.parent.model.attachments().findWhere({filename: filename});
      }

      this.insertImageBox.show(function(image) {
        self.grammarModel.insertImageAtCursor(self.textEditor, 'media/' + image.get('filename'));
        self.textEditor.focus();
      }, selected);
    },

    getAmendingWork: function(document) {
      var date = document.get('expression_date'),
          documentAmendments = Indigo.Preloads.amendments,
          amendment = _.findWhere(documentAmendments, {date: date});

      if (amendment) {
        return amendment.amending_work;
      }

    },

    insertRemark: function(e) {
      e.preventDefault();
      var amendedSection = this.fragment.id.replace('-', ' '),
          verb = e.currentTarget.getAttribute('data-verb'),
          amendingWork = this.getAmendingWork(this.parent.model),
          remark = '<remark>';

      if (this.remarkGenerator && amendingWork) {
        remark = this.remarkGenerator(this.parent.model, amendedSection, verb, amendingWork, this.grammarModel);
      }

      this.grammarModel.insertRemark(this.textEditor, remark);
      this.textEditor.focus();
    },

    resize: function() {},
  });

  // Handle the document editor, tracking changes and saving it back to the server.
  Indigo.DocumentEditorView = Backbone.View.extend({
    el: 'body',
    events: {
      'click .btn.show-xml-editor': 'toggleShowXMLEditor',
      'click .btn.show-structure': 'toggleShowStructure',
      'click .show-pit-comparison': 'toggleShowComparison',
    },

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
      // XXX this is a deferred to indicate when the editor is ready to edit
      this.editorReady = this.sourceEditor.editorReady;
      this.editFragment(null);

      this.xmlEditor = new Indigo.XMLEditorView({parent: this, documentContent: this.documentContent});
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

        this.sourceEditor.editFragment(fragment);
        this.xmlEditor.editFragment(fragment);
      }
    },

    toggleShowXMLEditor: function(e) {
      var show = !$(e.currentTarget).hasClass('active');
      this.$el.find('.document-content-view').toggleClass('show-xml-editor', show);
      this.$el.find('.document-content-view .annotations-container').toggleClass('hide-annotations', show);
      if (show) {
        this.xmlEditor.show();
      } else {
        this.xmlEditor.hide();
      }
    },

    toggleShowStructure: function(e) {
      var show = !$(e.currentTarget).hasClass('active');
      this.$el.find('#document-sheet la-akoma-ntoso').toggleClass('show-structure', show);
    },

    toggleShowComparison: function(e) {
      var show = !e.currentTarget.classList.contains('active'),
          menuItem = e.currentTarget.parentElement.previousElementSibling;

      $(e.currentTarget).siblings().removeClass('active');
      this.sourceEditor.setComparisonDocumentId(show ? e.currentTarget.getAttribute('data-id') : null);
      e.currentTarget.classList.toggle('active');

      menuItem.classList.toggle('btn-outline-secondary', !show);
      menuItem.classList.toggle('btn-primary', show);
    },

    removeFragment: function(fragment) {
      fragment = fragment || this.fragment;
      this.documentContent.replaceNode(fragment, null);
    },

    updateFragment: function(oldNode, newNodes) {
      this.updating = true;
      try {
        var updated = this.documentContent.replaceNode(oldNode, newNodes);
        if (oldNode == this.fragment) {
          this.fragment = updated;
          this.sourceEditor.editFragment(updated);
          this.xmlEditor.editFragment(updated);
        }
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
      return this.dirty || this.sourceEditor.editing;
    },

    canCancelEdits: function() {
      return (!this.sourceEditor.editing || confirm("You will lose your changes, are you sure?"));
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
        this.sourceEditor
          // ask the editor to returns its contents
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
