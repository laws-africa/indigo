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
      this.model.on('change:title', this.setWindowTitle);
    },

    setWindowTitle: function() {
      document.title = this.get('title');
    },

    render: function(title) {
      var html = this.model.get('title');

      if (this.model.get('draft')) {
        html = html + ' <span class="label label-warning">draft</span>';
      }

      return html;
    },
  });

  // Handle the document properties form, and saving them back to the server.
  Indigo.DocumentPropertiesView = Backbone.View.extend({
    el: '#props-tab article',
    bindings: {
      '#document_title': 'title',
      '#document_country': 'country',
      '#document_uri': 'uri',
      '#document_publication_date': 'publication_date',
      '#document_publication_name': 'publication_name',
      '#document_publication_number': 'publication_number',
      '#document_number': 'number',
      '#document_nature': 'nature',
      '#document_draft': {
        observe: 'draft',
        // API requires this value to be true or false
        onSet: function(val) { return val == "1"; }
      },
      '#document_updated_at': {
        observe: 'updated_at',
        onGet: function(value, options) {
          return moment(value).calendar();
        }
      },
      '#document_created_at': {
        observe: 'created_at',
        onGet: function(value, options) {
          return moment(value).calendar();
        }
      },
    },

    initialize: function() {
      this.stickit();

      this.dirty = false;
      this.model.on('change', this.setDirty, this);
      this.model.on('sync', this.setClean, this);

      // only attach URI building handlers after the first sync
      this.listenToOnce(this.model, 'sync', function() {
        this.model.on('change:number change:nature change:country change:publication_date', _.bind(this.calculateUri, this));
      });
    },

    calculateUri: function() {
      // rebuild the FRBR uri when one of its component sources changes
      var parts = [
        '',
        this.model.get('country'),
        this.model.get('nature'),
        this.model.get('publication_date').split('-')[0],
        this.model.get('number'),
        ''];
      this.model.set('uri', parts.join('/'));
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

    save: function() {
      // TODO: validation
      var self = this;

      // don't do anything if it hasn't changed
      if (!this.dirty) {
        return $.Deferred().resolve();
      }

      return this.model
        .save()
        .done(function() {
          self.model.attributes.updated_at = moment().format();
        });
    },
  });

  // Handle the document body editor, tracking changes and saving it back to the server.
  Indigo.DocumentBodyEditorView = Backbone.View.extend({
    el: '#content-tab',

    initialize: function() {
      // setup ace editor
      this.editor = ace.edit(this.$el.find(".ace-editor")[0]);
      this.editor.setTheme("ace/theme/monokai");
      this.editor.getSession().setMode("ace/mode/xml");
      this.editor.setValue();
      this.editor.$blockScrolling = Infinity;
      this.editor.on('change', _.debounce(_.bind(this.updateDocumentBody, this), 500));

      this.dirty = false;
      this.model.on('change', this.setDirty, this);
      this.model.on('sync', this.setClean, this);

      this.model.on('change', this.updateEditor, this);
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

    save: function() {
      // TODO: validation

      // don't do anything if it hasn't changed
      if (!this.dirty) {
        return $.Deferred().resolve();
      }

      return this.model.save();
    },

    updateEditor: function(model, options) {
      // update the editor with new content from the model,
      // unless this new content already comes from the editor
      if (!options.fromEditor) this.editor.setValue(this.model.get('body_xml'));
    },

    updateDocumentBody: function() {
      // update the document content from the editor's version
      console.log('new body_xml content');
      this.model.set(
        {body_xml: this.editor.getValue()},
        {fromEditor: true}); // prevent infinite loop
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
  //   DocumentBodyEditorView - handles editing the document's body content
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
      'click .btn.save': 'save',
      'shown.bs.tab a[href="#preview-tab"]': 'renderPreview',
    },

    initialize: function() {
      var library = new Indigo.Library(),
          document_id = $('[data-document-id]').data('document-id') || null;

      this.$saveBtn = $('.btn.save');

      var info = document_id ? {id: document_id} : {
        id: null,
        title: '(untitled)',
        publication_date: moment().format('YYYY-MM-DD'),
        nature: 'act',
        country: 'za',
        number: '1',
      };

      this.document = new Indigo.Document(info, {collection: library});
      this.document.on('change', this.setDirty, this);
      this.document.on('sync', this.setModelClean, this);

      this.documentBody = new Indigo.DocumentBody({id: document_id});
      this.documentBody.on('change', this.setDirty, this);

      this.user = Indigo.userView.model;
      this.user.on('change', this.userChanged, this);

      this.previewDirty = true;

      this.titleView = new Indigo.DocumentTitleView({model: this.document});
      this.propertiesView = new Indigo.DocumentPropertiesView({model: this.document});
      this.propertiesView.on('dirty', this.setDirty, this);
      this.propertiesView.on('clean', this.setClean, this);

      this.bodyEditorView = new Indigo.DocumentBodyEditorView({model: this.documentBody});
      this.bodyEditorView.on('dirty', this.setDirty, this);
      this.bodyEditorView.on('clean', this.setClean, this);

      // prevent the user from navigating away without saving changes
      $(window).on('beforeunload', _.bind(this.windowUnloading, this));

      if (document_id) {
        // fetch it
        this.document.fetch();
        this.documentBody.fetch();
      } else {
        // pretend we've fetched it, this sets up additional handlers
        this.document.trigger('sync');
        this.documentBody.trigger('sync');
        this.propertiesView.calculateUri();
        this.setDirty();
      }
    },

    windowUnloading: function(e) {
      if (this.propertiesView.dirty || this.bodyEditorView.dirty) {
        e.preventDefault();
        return 'You will lose your changes!';
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
          .prop('disabled', true);
      }
    },

    userChanged: function() {
      this.$saveBtn.toggle(this.user.authenticated());
    },

    save: function() {
      var self = this;
      var failed = function(request) {
        self.$saveBtn.prop('disabled', false);
      };

      this.$saveBtn.prop('disabled', true);

      this.propertiesView
        .save()
        .then(function() {
          self.bodyEditorView
            .save()
            .fail(failed);
        })
        .fail(failed);
    },

    renderPreview: function() {
      if (this.previewDirty) {
        var self = this,
            data = this.document.toJSON();

        data.body_xml = this.documentBody.get('body_xml');
        data = JSON.stringify({'document': data});

        $.ajax({
          url: '/api/render',
          type: "POST",
          data: data,
          contentType: "application/json; charset=utf-8",
          dataType: "json"})
          .then(function(response) {
            $('#preview-tab .an-container').html(response.html);
            self.previewDirty = false;
          });
      }
    },
  });
})(window);
