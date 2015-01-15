(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.DocumentTitleView = Backbone.View.extend({
    el: $('.workspace-header'),
    bindings: {
      'h4': 'title'
    },

    initialize: function() {
      this.stickit();
      this.model.on('change:title', this.setWindowTitle);
    },

    setWindowTitle: function() {
      document.title = this.get('title');
    },
  });

  Indigo.DocumentPropertiesView = Backbone.View.extend({
    el: $('#props-tab article'),
    bindings: {
      '#document_title': 'title',
      '#document_country': 'country',
      '#document_uri': 'uri',
      '#document_draft': {
        observe: 'draft',
        onSet: function(val) {
          // API requires true or false
          return val == "1";
        }
      }
    },

    initialize: function() {
      this.stickit();
    }
  });

  Indigo.DocumentContentEditorView = Backbone.View.extend({
    el: $('#content-tab'),

    initialize: function() {
      // setup ace editor
      this.editor = ace.edit(this.$el.find(".ace-editor")[0]);
      this.editor.setTheme("ace/theme/monokai");
      this.editor.getSession().setMode("ace/mode/xml");
      this.editor.setValue();

      this.model.on('change:document_xml', this.updateEditor, this);
      this.editor.on('change', $.proxy(this.updateDocumentContent, this));
    },

    updateEditor: function(model, value, options) {
      if (!options.fromEditor) this.editor.setValue(this.model.get('document_xml'));
    },

    updateDocumentContent: function() {
      this.model.set(
        {document_xml: this.editor.getValue()},
        {fromEditor: true});
    },
  });

  Indigo.DocumentView = Backbone.View.extend({
    el: $('body'),
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

    save: function() {
      if (this.model.isValid()) {
        var btn = this.$el.find('.btn.save'),
            self = this;

        btn.prop('disabled', true);

        this.model
          .save()
          .fail(function(request) {
            btn.prop('disabled', false);
            Indigo.errorView.show(request.responseText || request.statusText);
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
