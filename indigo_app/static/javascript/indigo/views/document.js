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
  //   DocumentEditorView - handles editing the document's body content
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
      'click .workspace-buttons .btn.save': 'save',
      'click .btn.delete-document': 'delete',
      'hidden.bs.tab a[href="#content-tab"]': 'tocDeselected',
      'shown.bs.tab a[href="#preview-tab"]': 'renderPreview',
      'click .btn.clone': 'createClone',
    },

    initialize: function() {
      var library = new Indigo.Library(),
          document_id = $('[data-document-id]').data('document-id') || null;

      this.$saveBtn = $('.workspace-buttons .btn.save');

      // The document page eager loads the document details into this
      // variable.
      var info = Indigo.documentPreload;

      this.document = new Indigo.Document(info, {collection: library, parse: true});
      this.document.on('change', this.setDirty, this);
      this.document.on('change', this.allowDelete, this);

      this.documentContent = new Indigo.DocumentContent({id: document_id});
      this.documentContent.on('change', this.documentContentChanged, this);

      this.documentDom = new Indigo.DocumentDom();
      this.documentDom.on('change', this.setDirty, this);

      this.user = Indigo.userView.model;
      this.user.on('change', this.userChanged, this);

      this.previewDirty = true;

      this.titleView = new Indigo.DocumentTitleView({model: this.document});
      this.propertiesView = new Indigo.DocumentPropertiesView({model: this.document});
      this.propertiesView.on('dirty', this.setDirty, this);
      this.propertiesView.on('clean', this.setClean, this);

      this.amendmentsView = new Indigo.DocumentAmendmentsView({model: this.document});

      this.tocView = new Indigo.DocumentTOCView({model: this.documentDom});
      this.tocView.on('item-selected', this.showEditor, this);

      this.bodyEditorView = new Indigo.DocumentEditorView({
        model: this.document,
        xmlModel: this.documentDom,
        rawModel: this.documentContent,
        tocView: this.tocView,
      });
      this.bodyEditorView.on('dirty', this.setDirty, this);
      this.bodyEditorView.on('clean', this.setClean, this);

      // prevent the user from navigating away without saving changes
      $(window).on('beforeunload', _.bind(this.windowUnloading, this));

      // pretend we've fetched it, this sets up additional handlers
      this.document.trigger('sync');

      if (document_id) {
        // fetch content
        this.documentContent.fetch();
      } else {
        this.documentContent.trigger('sync');
        this.propertiesView.calculateUri();
        this.setDirty();
      }
    },

    documentContentChanged: function() {
      this.documentDom.setXml(prettyPrintXml(this.documentContent.get('content')));
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

      if (this.$saveBtn.prop('disabled')) {
        this.$saveBtn
          .removeClass('btn-default')
          .addClass('btn-info')
          .prop('disabled', false);
      }
    },

    setClean: function() {
      // disable the save button if both views are clean
      if (!this.propertiesView.dirty && !this.bodyEditorView.dirty) {
        this.$saveBtn
          .addClass('btn-default')
          .removeClass('btn-info')
          .prop('disabled', true)
          .find('.fa')
            .removeClass('fa-pulse fa-spinner')
            .addClass('fa-save');
      }
    },

    allowDelete: function() {
      this.$el.find('.btn.delete-document').prop('disabled',
        this.document.isNew() || !this.user.authenticated() || !this.document.get('draft'));
    },

    userChanged: function() {
      this.$saveBtn.toggle(this.user.authenticated());
      this.allowDelete();
    },

    save: function() {
      var self = this;
      var is_new = self.document.isNew();
      var failed = function(request) {
        self.$saveBtn
          .prop('disabled', false)
          .find('.fa')
            .removeClass('fa-pulse fa-spinner')
            .addClass('fa-save');
      };

      this.$saveBtn
        .prop('disabled', true)
        .find('.fa')
          .removeClass('fa-save')
          .addClass('fa-pulse fa-spinner');

      // We save the content first, and then save
      // the properties on top of it, so that content
      // properties that change metadata in the content
      // take precendence.

      this.bodyEditorView
        .save()
        .then(function(response) {
          self.propertiesView
            .save()
            .fail(failed)
            .then(function() {
              if (is_new) {
                // redirect
                document.location = '/documents/' + response.id + '/';
              }
            });
        })
        .fail(failed);
    },

    renderPreview: function() {
      if (this.previewDirty) {
        var self = this,
            data = this.document.toJSON();

        data.content = this.documentDom.toXml();
        data = JSON.stringify({
          'inputformat': 'application/json',
          'outputformat': 'text/html',
          'content': data});

        $.ajax({
          url: '/api/convert',
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
      if (confirm('Are you sure you want to delete this document?')) {
        this.document
          .destroy()
          .then(function() {
            document.location = '/library';
          });
      }
    },

    // Create a clone of the document and redirect them there
    createClone: function(e) {
      if (confirm('Create a copy of this document? Unsaved changes will be lost!')) {
        // clone and reset some attributes
        var clone = this.document.clone();
        clone.set({
          content: this.documentContent.get('content'),
          draft: true,
          title: 'Copy of ' + clone.get('title'),
          id: null,
        });

        var $btn = $(e.target);
        $btn
          .toggleClass('disabled')
          .find('.fa')
          .toggleClass('fa-copy fa-pulse fa-spinner');

        clone
          .save(null, {parse: false})
          .done(function(response) {
            // redirect
            document.location = '/documents/' + response.id + '/';
          })
          .fail(function() {
            $btn
              .toggleClass('disabled')
              .find('.fa')
              .toggleClass('fa-copy fa-pulse fa-spinner');
          });
      }
    }
  });
})(window);
