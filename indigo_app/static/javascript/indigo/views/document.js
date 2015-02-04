(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

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
      }
    },

    initialize: function() {
      this.stickit();
    }
  });

  Indigo.DocumentContentEditorView = Backbone.View.extend({
    el: '#content-tab',

    initialize: function() {
      // setup ace editor
      this.editor = ace.edit(this.$el.find(".ace-editor")[0]);
      this.editor.setTheme("ace/theme/monokai");
      this.editor.getSession().setMode("ace/mode/xml");
      this.editor.setValue();

      this.model.on('change:body_xml', this.updateEditor, this);
      this.editor.on('change', _.debounce(
        $.proxy(this.updateDocumentContent, this),
        500));

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

    updateEditor: function(model, value, options) {
      // update the editor with new content from the model,
      // unless this new content already comes from the editor
      if (!options.fromEditor) this.editor.setValue(this.model.get('body_xml'));
    },

    updateDocumentContent: function() {
      // update the document content from the editor's version
      console.log('new body_xml content');
      this.model.set(
        {body_xml: this.editor.getValue()},
        {fromEditor: true}); // prevent infinite loop
    },
  });

  Indigo.DocumentView = Backbone.View.extend({
    el: 'body',
    events: {
      'click .btn.save': 'save',
      'shown.bs.tab a[href="#preview-tab"]': 'renderPreview',
    },

    initialize: function() {
      var library = new Indigo.Library();

      var document_id = $('[data-document-id]').data('document-id');
      this.model = new Indigo.Document({id: document_id}, {
        collection: library
      });

      this.model.dirty = false;
      this.model.on('change', this.setModelDirty, this);
      this.model.on('sync', this.setModelClean, this);

      this.user = Indigo.userView.model;
      this.user.on('change', this.userChanged, this);

      new Indigo.DocumentTitleView({model: this.model});
      new Indigo.DocumentPropertiesView({model: this.model});
      new Indigo.DocumentContentEditorView({model: this.model});

      this.model.fetch();
    },

    setModelDirty: function() {
      if (!this.model.dirty) {
        this.model.dirty = true;

        $('.btn.save')
          .removeClass('btn-default')
          .addClass('btn-info')
          .prop('disabled', false);
      }
    },

    setModelClean: function() {
      if (this.model.dirty) {
        this.model.dirty = false;

        $('.btn.save')
          .addClass('btn-default')
          .removeClass('btn-info')
          .prop('disabled', true);
      }
    },

    userChanged: function() {
      $('.btn.save').toggle(this.user.authenticated());
    },

    save: function() {
      if (this.model.isValid()) {
        var btn = this.$el.find('.btn.save'),
            self = this;

        btn.prop('disabled', true);

        this.model
          .save()
          .fail(function(request) {
            btn.prop('disabled', false);
            if (request.status == 403) {
              Indigo.errorView.show("You aren't allowed to save. Try logging out and in again.");
            } else {
              Indigo.errorView.show(request.responseText || request.statusText);
            }
          });
      }
    },

    renderPreview: function() {
      var data = JSON.stringify({'document': this.model.toJSON()});

      $.ajax({
        url: '/api/render',
        type: "POST",
        data: data,
        contentType: "application/json; charset=utf-8",
        dataType: "json"})
        .then(function(response) {
          $('#preview-tab .an-container').html(response.html);
        });
    },
  });
})(window);
