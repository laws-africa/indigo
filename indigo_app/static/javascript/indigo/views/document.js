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

      this.listenTo(this.model, 'change:title change:expression_date change:draft sync change:frbr_uri', this.render);
      this.listenTo(this.expressions, 'sync change reset', this.render);
    },

    getTitle: function() {
      return this.model.get('title') + ' @ ' + this.model.get('expression_date');
    },

    render: function() {
      var title = this.getTitle();

      document.title = title;
      $('.document-title').text(title);

      // breadcrumb
      var country = Indigo.countries[this.model.get('country')],
          locality = this.model.get('locality'),
          dates = _.unique(this.expressions.pluck('expression_date')),
          docs = this.expressions,
          current_id = this.model.get('id');
      locality = locality ? country.localities[locality] : null;
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
        country: country,
        locality: locality,
        work: this.model.work.toJSON(),
        expressions: expressions,
      }));
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
  //   DocumentRepealView - handles setting a document as repealed
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
      'click .menu .dropdown-submenu > a': 'stopMenuClick',
      'click .document-workspace-buttons .btn.save': 'save',
      'click .document-workspace-buttons .save-and-publish': 'saveAndPublish',
      'click .document-workspace-buttons .save-and-unpublish': 'saveAndUnpublish',
      'click .document-toolbar-menu .save': 'save',
      'click .document-toolbar-menu .delete-document': 'delete',
      'click .document-toolbar-menu .clone-document': 'clone',
      'click .document-toolbar-menu .change-document-work': 'changeWork',
      'click .sidebar-nav .show-preview': 'showPreview',
    },

    initialize: function() {
      var library = Indigo.library,
          self = this;

      this.$saveBtn = $('.document-workspace-buttons .btn.save');
      this.$menu = $('.document-toolbar-menu');
      this.dirty = false;
      this.previewDirty = true;

      // stop disable menus
      $('.menu').on('click', '.disabled a', _.bind(this.stopMenuClick));

      // get it from the library
      this.document = new Indigo.Document(Indigo.Preloads.document);
      this.document.work = new Indigo.Work(Indigo.Preloads.work);

      this.document.on('change', this.setDirty, this);
      this.document.on('change:draft', this.draftChanged, this);

      this.documentContent = new Indigo.DocumentContent({document: this.document});
      this.documentContent.on('change', this.setDirty, this);

      this.titleView = new Indigo.DocumentTitleView({model: this.document});
      this.propertiesView = new Indigo.DocumentPropertiesView({model: this.document});
      this.propertiesView.on('dirty', this.setDirty, this);
      this.propertiesView.on('clean', this.setClean, this);

      this.attachmentsView = new Indigo.DocumentAttachmentsView({document: this.document});
      this.attachmentsView.on('dirty', this.setDirty, this);
      this.attachmentsView.on('clean', this.setClean, this);

      this.definedTermsView = new Indigo.DocumentDefinedTermsView({model: this.documentContent});
      this.referencesView = new Indigo.DocumentReferencesView({model: this.documentContent});
      this.revisionsView = new Indigo.DocumentRevisionsView({document: this.document, documentContent: this.documentContent});
      this.tocView = new Indigo.DocumentTOCView({model: this.documentContent});

      this.bodyEditorView = new Indigo.DocumentEditorView({
        model: this.document,
        documentContent: this.documentContent,
        tocView: this.tocView,
      });
      this.bodyEditorView.on('dirty', this.setDirty, this);
      this.bodyEditorView.on('clean', this.setClean, this);
      this.bodyEditorView.editorReady.then(function() {
        // select the first element in the toc
        self.tocView.selectItem(0, true);
      });

      this.annotationsView = new Indigo.DocumentAnnotationsView({model: this.document});
      this.annotationsView.listenTo(this.bodyEditorView.sourceEditor, 'rendered', this.annotationsView.renderAnnotations);

      this.activityView = new Indigo.DocumentActivityView({document: this.document});

      // pretend we've fetched it, this sets up additional handlers
      this.document.trigger('sync');

      // preload content and pretend this document is unchanged
      this.documentContent.set('content', Indigo.Preloads.documentContent);
      this.documentContent.trigger('sync');

      // make menu peers behave like real menus on hover
      $('.menu .btn-link').on('mouseover', function(e) {
        var $menuItem = $(this),
            $parent = $menuItem.parent();
            
        if (!$parent.hasClass("open") && $parent.siblings(".open").length) {
          $menuItem.click();
        }
      });
    },

    isDirty: function(e) {
      return this.propertiesView.dirty || this.bodyEditorView.isDirty();
    },

    setDirty: function() {
      // our preview is now dirty
      this.previewDirty = true;

      if (!this.dirty) {
        this.dirty = true;
        this.$saveBtn.prop('disabled', false);
        this.$menu.find('.save').removeClass('disabled');
      }
    },

    setClean: function() {
      // disable the save button if all views are clean
      if (!this.propertiesView.dirty && !this.bodyEditorView.dirty && !this.attachmentsView.dirty) {
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
      if (Indigo.user.hasPerm('indigo_api.publish_document') && confirm('Publish this document to users?')) {
        this.document.set('draft', false);
        this.save();
      }
    },

    saveAndUnpublish: function() {
      if (Indigo.user.hasPerm('indigo_api.publish_document') && confirm('Hide this document from users?')) {
        this.document.set('draft', true);
        this.save();
      }
    },

    save: function() {
      var self = this;
      var deferred = null;

      // always save properties if we save content
      this.propertiesView.dirty = this.propertiesView.dirty || this.bodyEditorView.dirty;

      var fail = function() {
        self.$saveBtn
          .prop('disabled', false)
          .find('.fa')
            .removeClass('fa-pulse fa-spinner')
            .addClass('fa-save');
        self.$menu.find('.save').removeClass('disabled');
      };

      this.$saveBtn
        .prop('disabled', true)
        .find('.fa')
          .removeClass('fa-save')
          .addClass('fa-pulse fa-spinner');
      this.$menu.find('.save').addClass('disabled');

      deferred = $.Deferred().resolve();

      // We save the content first, and then save
      // the properties on top of it, so that content
      // properties that change metadata in the content
      // take precendence.
      deferred.then(function() {
        self.bodyEditorView.save().then(function() {
          self.propertiesView.save().then(function() {
            self.attachmentsView.save().fail(fail);
          }).fail(fail);
        }).fail(fail);
      }).fail(fail);
    },

    showPreview: function(e) {
      var $link = $(e.currentTarget);

      if ($link.hasClass('active')) {
        this.closePreview();
        return;
      }

      $link.addClass('active');
      this.$('.work-view').addClass('d-none');
      this.$('.document-preview-view').removeClass('d-none');
      
      if (this.previewDirty) {
        var self = this,
            data = this.document.toJSON(),
            $container = $('.preview-container .akoma-ntoso').empty();

        $container[0].className = 'preview-container akoma-ntoso country-' + data.country;

        data.content = this.documentContent.toXml();
        data = JSON.stringify({'document': data});

        $.ajax({
          url: '/api/render',
          type: "POST",
          data: data,
          contentType: "application/json; charset=utf-8",
          dataType: "json"})
          .then(function(response) {
            $container.html(response.output);
            self.previewDirty = false;
          });
      }
    },

    closePreview: function() {
      this.$('.sidebar-nav .show-preview').removeClass('active');
      this.$('.work-view').removeClass('d-none');
      this.$('.document-preview-view').addClass('d-none');
    },

    delete: function() {
      if (!this.document.get('draft')) {
        alert('You cannot delete published documents. Please mark the document as a draft and try again.');
        return;
      }

      if (confirm('Are you sure you want to delete this document?')) {
        var frbr_uri = this.document.work.get('frbr_uri');

        Indigo.progressView.peg();
        this.document
          .destroy()
          .then(function() {
            document.location = '/works' + frbr_uri + '/';
          });
      }
    },

    clone: function() {
      if (confirm('Go ahead and create a copy of this document?')) {
        var clone = this.document.clone();
        clone.set({
          draft: true,
          id: null,
          content: this.documentContent.get('content'),
        });

        Indigo.progressView.peg();
        clone.save().then(function(doc) {
          document.location = '/documents/' + doc.id + '/';
        });
      }
    },

    changeWork: function(e) {
      if (!confirm("Are you sure you want to change the work this document is linked to?")) return;

      var document = this.document;
      var chooser = new Indigo.WorkChooserView({country: document.get('country')});

      chooser.choose(document.work);
      chooser.showModal().done(function(chosen) {
        if (chosen) {
          document.setWork(chosen);
        }
      });
    },

    stopMenuClick: function(e) {
      // stop menu clicks on disabled items from doing anything
      e.preventDefault();
      e.stopImmediatePropagation();
    },
  });
})(window);
