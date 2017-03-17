(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // Handle the rendering of the document title, and the browser window title
  Indigo.DocumentTitleView = Backbone.View.extend({
    el: '.workspace-header',
    bindings: {
      '.document-title': {
        observe: ['title', 'draft'],
        updateMethod: 'html',
        onGet: 'render',
      }
    },

    initialize: function() {
      this.stickit();
      this.model.on('change:title sync', this.setWindowTitle);
    },

    setWindowTitle: function() {
      document.title = this.get('title');
    },

    render: function(title) {
      var html = this.model.get('title');

      if (this.model.get('draft')) {
        html = html + ' <span class="label label-warning">draft</span>';
      } else {
        html = html + ' <span class="label label-info">published</span>';
      }

      return html;
    },
  });

  // The DocumentView is the primary view on the document detail page.
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
  //   DocumentAmendmentsView - handles editing document amendment metadata
  //
  //   DocumentAttachmentsView - handles managing document attachments
  //
  //   DocumentRepealView - handles setting a document as repealed
  //
  //   DocumentEditorView - handles editing the document's body content
  //
  //   DocumentRevisionsView - handles walking through revisions to a document
  //
  // When saving a document, the DocumentView tells the children to save their changes.
  // In turn, they trigger 'dirty' and 'clean' events when their models change or
  // once they've been saved. The DocumentView uses those signals to enable/disable
  // the save button.
  //
  //
  Indigo.DocumentView = Backbone.View.extend({
    el: 'body',
    events: {
      'click .menu .disabled a': 'stopMenuClick',
      'click .menu .dropdown-submenu > a': 'stopMenuClick',
      'click .workspace-buttons .btn.save': 'save',
      'click .menu .save a': 'save',
      'click .menu .delete-document a': 'delete',
      'click .menu .clone-document a': 'clone',
      'hidden.bs.tab a[href="#content-tab"]': 'tocDeselected',
      'shown.bs.tab a[href="#preview-tab"]': 'renderPreview',
    },

    initialize: function() {
      var library = Indigo.library,
          document_id = $('[data-document-id]').data('document-id') || null;

      this.$saveBtn = $('.workspace-buttons .btn.save');
      this.$menu = $('.workspace-header .menu');
      this.dirty = false;

      if (document_id) {
        // get it from the library
        this.document = Indigo.library.get(document_id);
      } else {
        // only for new documents
        this.document = new Indigo.Document(Indigo.Preloads.document, {collection: library, parse: true});
        Indigo.library.add(this.document);
      }

      this.document.on('change', this.setDirty, this);
      this.document.on('change', this.allowDelete, this);
      this.document.expressionSet = Indigo.library.expressionSet(this.document);

      this.documentContent = new Indigo.DocumentContent({document: this.document});
      this.documentContent.on('change', this.setDirty, this);
      
      this.user = Indigo.userView.model;
      this.user.on('change', this.userChanged, this);

      this.previewDirty = true;

      this.titleView = new Indigo.DocumentTitleView({model: this.document});
      this.propertiesView = new Indigo.DocumentPropertiesView({model: this.document});
      this.propertiesView.on('dirty', this.setDirty, this);
      this.propertiesView.on('clean', this.setClean, this);

      this.amendmentsView = new Indigo.DocumentAmendmentsView({model: this.document});
      this.repealView = new Indigo.DocumentRepealView({model: this.document});

      this.attachmentsView = new Indigo.DocumentAttachmentsView({document: this.document});
      this.attachmentsView.on('dirty', this.setDirty, this);
      this.attachmentsView.on('clean', this.setClean, this);

      this.definedTermsView = new Indigo.DocumentDefinedTermsView({model: this.documentContent});

      this.revisionsView = new Indigo.DocumentRevisionsView({document: this.document, documentContent: this.documentContent});

      this.tocView = new Indigo.DocumentTOCView({model: this.documentContent});
      this.tocView.on('item-selected', this.showEditor, this);

      this.bodyEditorView = new Indigo.DocumentEditorView({
        model: this.document,
        documentContent: this.documentContent,
        tocView: this.tocView,
      });
      this.bodyEditorView.on('dirty', this.setDirty, this);
      this.bodyEditorView.on('clean', this.setClean, this);

      // prevent the user from navigating away without saving changes
      $(window).on('beforeunload', _.bind(this.windowUnloading, this));

      // pretend we've fetched it, this sets up additional handlers
      this.document.trigger('sync');

      // preload content
      this.documentContent.set('content', Indigo.Preloads.documentContent);

      if (document_id) {
        // pretend this document is unchanged
        this.documentContent.trigger('sync');
      } else {
        // new document, pretend it's dirty
        this.propertiesView.calculateUri();
        this.setDirty();
      }

      // make menu peers behave like real menus on hover
      $('.menu .btn-link').on('mouseover', function(e) {
        var $menuItem = $(this),
            $parent = $menuItem.parent();
            
        if (!$parent.hasClass("open") && $parent.siblings(".open").length) {
          $menuItem.click();
        }
      });
    },

    windowUnloading: function(e) {
      if (this.propertiesView.dirty || this.bodyEditorView.dirty) {
        e.preventDefault();
        return 'You will lose your changes!';
      }
    },

    showEditor: function(item) {
      if (item) {
        this.$el.find('a[href="#content-tab"]').click();
      }
    },

    setDirty: function() {
      // our preview is now dirty
      this.previewDirty = true;

      if (!this.dirty) {
        this.dirty = true;
        this.$saveBtn
          .removeClass('btn-default')
          .addClass('btn-info')
          .prop('disabled', false);
        this.$menu.find('.save').removeClass('disabled');
      }
    },

    setClean: function() {
      // disable the save button if all views are clean
      if (!this.propertiesView.dirty && !this.bodyEditorView.dirty && !this.attachmentsView.dirty) {
        this.dirty = false;
        this.$saveBtn
          .addClass('btn-default')
          .removeClass('btn-info')
          .prop('disabled', true)
          .find('.fa')
            .removeClass('fa-pulse fa-spinner')
            .addClass('fa-save');
        this.$menu.find('.save').addClass('disabled');
      }
    },

    allowDelete: function() {
      this.$menu.find('.delete-document').toggleClass('disabled',
        this.document.isNew() || !this.user.authenticated());
    },

    userChanged: function() {
      this.$saveBtn.toggle(this.user.authenticated());
      this.allowDelete();
    },

    save: function() {
      var self = this;
      var is_new = self.document.isNew();
      var deferred = null;

      // always save properties if we save content
      this.propertiesView.dirty = this.propertiesView.dirty || this.bodyEditorView.dirty || is_new;

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

      if (is_new) {
        // save properties first, to get an ID, then
        // stash the ID and save the rest
        deferred = this.propertiesView.save(true);
      } else {
        deferred = $.Deferred().resolve();
      }

      // We save the content first, and then save
      // the properties on top of it, so that content
      // properties that change metadata in the content
      // take precendence.
      deferred.then(function() {
        self.bodyEditorView.save().then(function() {
          self.propertiesView.save().then(function() {
            self.attachmentsView.save().then(function() {
              if (is_new) {
                // redirect
                Indigo.progressView.peg();
                document.location = '/documents/' + self.document.get('id') + '/';
              }
            }).fail(fail);
          }).fail(fail);
        }).fail(fail);
      }).fail(fail);
    },

    renderPreview: function() {
      if (this.previewDirty) {
        var self = this,
            data = this.document.toJSON();

        data.content = this.documentContent.toXml();
        data = JSON.stringify({'document': data});

        $.ajax({
          url: '/api/render',
          type: "POST",
          data: data,
          contentType: "application/json; charset=utf-8",
          dataType: "json"})
          .then(function(response) {
            $('#preview-tab .akoma-ntoso').html(response.output);
            self.previewDirty = false;
          });
      }
    },

    tocDeselected: function(e) {
      this.tocView.trigger('deselect');
    },

    delete: function() {
      if (!this.document.get('draft')) {
        alert('You cannot delete published documents. Please mark the document as a draft and try again.');
        return;
      }

      if (confirm('Are you sure you want to delete this document?')) {
        Indigo.progressView.peg();
        this.document
          .destroy()
          .then(function() {
            document.location = '/library';
          });
      }
    },

    clone: function() {
      var title = prompt('Name for the copy', 'Copy of ' + this.document.get('title'));

      if (title) {
        var clone = this.document.clone();
        clone.set({
          draft: true,
          title: title,
          id: null,
          content: this.documentContent.get('content'),
        });

        Indigo.progressView.peg();
        clone.save().then(function(doc) {
          document.location = '/documents/' + doc.id + '/';
        });
      }
    },

    stopMenuClick: function(e) {
      // stop menu clicks on disabled items from doing anything
      e.preventDefault();
      e.stopImmediatePropagation();
    },
  });
})(window);
