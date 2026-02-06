(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // Handle the rendering of the document title, and the browser window title
  Indigo.DocumentTitleView = Backbone.View.extend({
    el: '.main-header',
    breadcrumbTemplate: '#breadcrumb-template',

    initialize: function() {
      this.breadcrumbTemplate = Handlebars.compile($(this.breadcrumbTemplate).html());
      this.expressions = new Indigo.Library(Indigo.Preloads.expressions);
      // ensure that this.model is in the expression list, not a duplicate
      this.expressions.remove(this.expressions.get(this.model.get('id')));
      this.expressions.add(this.model);

      this.listenTo(this.model, 'change:title change:expression_date change:draft sync', this.render);
      this.listenTo(this.expressions, 'sync change reset', this.render);
    },

    getTitle: function() {
      let title = this.model.get('title') + ' @ ' + this.model.get('expression_date');
      if (Indigo.Preloads.provisionEid) {
        title = title + ` – ${Indigo.Preloads.provisionEid}`;
      }
      return title;
    },

    render: function() {
      var title = this.getTitle();

      document.title = title;
      $('.document-title').text(title);

      // breadcrumb
      var dates = _.unique(this.expressions.pluck('expression_date')),
          docs = this.expressions,
          current_id = this.model.get('id');
      dates.sort();
      dates.reverse();

      var expressions = _.map(dates, function(date) {
        return {
          date: date,
          documents: _.map(docs.where({expression_date: date}), function(d) {
            d = d.toJSON();
            d.current = current_id == d.id;
            return d;
          })
        };
      });

      this.$('.breadcrumb').html(this.breadcrumbTemplate({
        document: this.model.toJSON(),
        expressions: expressions,
      }));
    },
  });

  Indigo.CheatsheetView = Backbone.View.extend({
    el: '#cheatsheet-modal',
    events: {
      'change .search': 'search',
      'keyup .search': 'search',
      'shown.bs.modal': 'shown',
    },

    search: function() {
      var needle = this.$('.search').val().trim().toLocaleLowerCase();

      if (needle.length > 0) {
        this.$('.card')
          .addClass('d-none')
          .each(function(i, card) {
            if (card.innerText.toLocaleLowerCase().indexOf(needle) > -1) {
              card.classList.remove('d-none');
            }
          });
      } else {
        this.$('.card').removeClass('d-none');
      }
    },

    shown: function(e) {
      this.$('.search').focus();
    },
  });

  // The DocumentDetailView is the primary view on the document detail page.
  // It is responsible for managing the other views and allowing the user to
  // save their changes. It has nested sub views that handle separate portions
  // of the larger view page.
  //
  //   DocumentTitleView - handles rendering the title of the document when it changes,
  //                       including updating the browser page title
  //
  //   DocumentPropertiesView - handles editing the document metadata, such as
  //                            publication dates and URIs
  //
  //   DocumentAttachmentsView - handles managing document attachments
  //
  //   DocumentEditorView - handles editing the document's body content
  //
  //   DocumentRevisionsView - handles walking through revisions to a document
  //
  // When saving a document, the DocumentDetailView tells the children to save their changes.
  // In turn, they trigger 'dirty' and 'clean' events when their models change or
  // once they've been saved. The DocumentDetailView uses those signals to enable/disable
  // the save button.
  //
  //
  Indigo.DocumentDetailView = Backbone.View.extend({
    el: 'body',
    events: {
      'click .dropdown-submenu > a': 'stopMenuClick',
      'click .document-workspace-buttons .btn.save': 'save',
      'click .document-workspace-buttons .save-and-publish': 'saveAndPublish',
      'click .document-workspace-buttons .save-and-unpublish': 'saveAndUnpublish',
      'click .document-toolbar-wrapper .delete-document': 'delete',
      'click .document-secondary-pane-toggle': 'toggleDocumentSecondaryPane',
      'indigo:pane-toggled': 'onPaneToggled',
    },

    initialize: function() {
      let self = this;

      this.$saveBtn = $('.document-workspace-buttons .btn.save');
      this.$menu = $('.document-toolbar-menu');
      this.secondaryPaneToggle = this.el.querySelector('.document-toolbar-wrapper .document-secondary-pane-toggle');
      this.dirty = false;
      Indigo.offlineNoticeView.autoShow();

      this.panes = {
        'document-secondary-pane': document.querySelector('.document-secondary-pane')
      };
      this.splitters = {
        'document-secondary-pane': this.panes['document-secondary-pane'].previousElementSibling
      };

      this.detectUnsupportedBrowsers();

      // stop disable menus
      $('.menu').on('click', '.disabled a', _.bind(this.stopMenuClick));

      // get it from the library
      this.document = new Indigo.Document(Indigo.Preloads.document);
      this.document.work = new Indigo.Work(Indigo.Preloads.work);
      this.document.issues = new Backbone.Collection();

      this.document.on('sync', this.setClean, this);
      this.document.on('change', this.setDirty, this);
      this.document.on('change:draft', this.draftChanged, this);

      this.documentContent = new Indigo.DocumentContent({document: this.document});
      this.documentContent.on('change', this.setDirty, this);

      this.cheatsheetView = new Indigo.CheatsheetView();
      this.titleView = new Indigo.DocumentTitleView({model: this.document});
      this.propertiesView = new Indigo.DocumentPropertiesView({model: this.document});

      this.attachmentsView = new Indigo.DocumentAttachmentsView({document: this.document});
      this.attachmentsView.on('dirty', this.setDirty, this);
      this.attachmentsView.on('clean', this.setClean, this);
      this.sourceAttachmentsView = new Indigo.SourceAttachmentView({document: this.document});

      this.definedTermsView = new Indigo.DocumentDefinedTermsView({model: this.documentContent});
      this.referencesView = new Indigo.DocumentReferencesView({model: this.documentContent});
      this.italicsView = new Indigo.DocumentItalicsView({model: this.documentContent});
      this.sentenceCaseView = new Indigo.DocumentSentenceCaseView({model: this.documentContent});
      this.revisionsView = new Indigo.DocumentRevisionsView({document: this.document, documentContent: this.documentContent});
      this.tocView = new Indigo.DocumentTOCView({model: this.documentContent, document: this.document});
      this.tocView.selection.on('change', this.onTocSelectionChanged, this);

      const queryParams = new URLSearchParams(window.location.search);

      this.sourceEditorView = new Indigo.SourceEditorView({
        model: this.document,
        tocView: this.tocView,
      });
      this.sourceEditorView.editorReady.then(function() {
        // select the appropriate element in the toc
        // TODO: there's a race condition here: the TOC might not be built yet
        if (queryParams.get("toc") && self.tocView.selectItemById(queryParams.get("toc"))) {
          return;
        }
        self.tocView.selectItem(0, true);
      });

      this.annotationsView = new Indigo.DocumentAnnotationsView({
        model: this.document,
        prefocus: parseInt(queryParams.get("anntn")),
      });
      this.annotationsView.listenTo(this.sourceEditorView, 'rendered', this.annotationsView.renderAnnotations);

      this.activityView = new Indigo.DocumentActivityView({document: this.document});
      this.issuesView = new Indigo.DocumentIssuesView({
        document: this.document,
        documentContent: this.documentContent,
        editorView: this.sourceEditorView,
      });

      const akn = this.el.querySelector('.document-primary-pane-content-pane la-akoma-ntoso');
      this.popupManager = new window.indigoAkn.PopupEnrichmentManager(akn);
      this.popupManager.addProvider(new window.enrichments.PopupIssuesProvider(this.document.issues, this.popupManager));

      // preload content and pretend this document is unchanged
      this.documentContent.set('content', Indigo.Preloads.documentContent);
      this.document.trigger('sync');

      // make menu peers behave like real menus on hover
      $('.menu .btn-link').on('mouseover', function(e) {
        var $menuItem = $(this),
            $parent = $menuItem.parent();
            
        if (!$parent.hasClass("open") && $parent.siblings(".open").length) {
          $menuItem.click();
        }
      });
    },

    detectUnsupportedBrowsers: function() {
      if (!('XSLTProcessor' in window)) {
        alert($t("Your browser is not supported by Indigo. Please use Chrome, Firefox, Safari or Edge instead."));
      }
    },

    isDirty: function(e) {
      return this.dirty || this.sourceEditorView.isDirty();
    },

    setDirty: function() {
      this.dirty = true;
      this.$saveBtn.prop('disabled', false);
      this.$menu.find('.save').removeClass('disabled');
    },

    setClean: function() {
      // disable the save button if all views are clean
      if (!this.sourceEditorView.isDirty() && !this.attachmentsView.dirty) {
        this.dirty = false;
        this.$saveBtn
          .prop('disabled', true)
          .find('.fa')
            .removeClass('fa-pulse fa-spinner')
            .addClass('fa-save');
        this.$menu.find('.save').addClass('disabled');
      }
    },

    draftChanged: function() {
      var draft = this.document.get('draft');

      $('body')
        .toggleClass('is-draft', draft)
        .toggleClass('is-published', !draft);

      this.$menu.find('.delete-document').toggleClass('disabled', !draft);
    },

    saveAndPublish: function() {
      if (Indigo.user.hasPerm('indigo_api.publish_document') && confirm($t('Publish this document to users?'))) {
        this.document.set('draft', false);
        this.save();
      }
    },

    saveAndUnpublish: function() {
      if (Indigo.user.hasPerm('indigo_api.publish_document') && confirm($t('Hide this document from users?'))) {
        this.document.set('draft', true);
        this.save();
      }
    },

    save: async function() {
      if (!this.sourceEditorView.confirmAndDiscardChanges()) return;

      this.$saveBtn
        .prop('disabled', true)
        .find('.fa')
          .removeClass('fa-save')
          .addClass('fa-pulse fa-spinner');

      try {
        // this saves the content and the document properties together
        await Indigo.deferredToAsync(this.documentContent.save());
        await Indigo.deferredToAsync(this.attachmentsView.save());

        // TODO: a better way of reloading the page (will redirect to provision chooser for now)
        if (this.sourceEditorView.aknTextEditor.reloadOnSave) {
          window.location.reload();
        }
      } catch {
        this.$saveBtn
          .prop('disabled', false)
          .find('.fa')
          .removeClass('fa-pulse fa-spinner')
          .addClass('fa-save');
      }
    },

    delete: function() {
      if (!this.document.get('draft')) {
        alert($t('You cannot delete published documents. Please mark the document as a draft and try again.'));
        return;
      }

      if (confirm($t('Are you sure you want to delete this document?'))) {
        var frbr_uri = this.document.work.get('frbr_uri');

        Indigo.progressView.peg();
        this.document
          .destroy()
          .then(function() {
            document.location = '/works' + frbr_uri + '/';
          });
      }
    },

    stopMenuClick: function(e) {
      // stop menu clicks on disabled items from doing anything
      e.preventDefault();
      e.stopImmediatePropagation();
    },

    showPane: function (pane) {
      if (this.panes[pane] && this.panes[pane].classList.contains('d-none')) {
        this.panes[pane].classList.remove('d-none');
        this.splitters[pane].classList.remove('d-none');
        this.el.dispatchEvent(new CustomEvent('indigo:pane-toggled', {detail: {pane, visible: true}}));
      }
    },

    hidePane: function (pane) {
      if (this.panes[pane] && !this.panes[pane].classList.contains('d-none')) {
        this.panes[pane].classList.add('d-none');
        this.splitters[pane].classList.add('d-none');
        this.el.dispatchEvent(new CustomEvent('indigo:pane-toggled', {detail: {pane, visible: false}}));
      }
    },

    togglePane: function (pane) {
      if (this.panes[pane]) {
        const hidden = this.panes[pane].classList.toggle('d-none');
        this.splitters[pane].classList.toggle('d-none', hidden);
        this.el.dispatchEvent(new CustomEvent('indigo:pane-toggled', {detail: {pane, visible: !hidden}}));
      }
    },

    toggleDocumentSecondaryPane: function () {
      this.togglePane('document-secondary-pane');
    },

    onPaneToggled: function (e) {
      if (e.originalEvent.detail.pane === 'document-secondary-pane') {
        this.secondaryPaneToggle.classList.toggle('active', e.originalEvent.detail.visible);
      }
    },

    onTocSelectionChanged: function (selection) {
      // update provision editor link
      const a = this.el.querySelector('.document-toolbar-wrapper .open-provision-editor');
      if (a) {
        a.disabled = true;
        a.classList.toggle('disabled', true);

        if (selection.get('element') && selection.get('element').getAttribute('eId')) {
          const eId = selection.get('element').getAttribute('eId');
          const href = `/documents/${this.document.get('id')}/provision/${eId}`;
          a.setAttribute('href', href);
          a.disabled = false;
          a.classList.remove('disabled');
        }
      }
    }
  });
})(window);
