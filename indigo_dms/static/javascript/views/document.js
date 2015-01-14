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
    },
  });

  Indigo.DocumentPropertiesView = Backbone.View.extend({
    el: $('#props-tab article'),
    bindings: {
      '#document_title': 'title',
      '#document_country': 'country',
      '#document_uri': 'uri',
    },

    initialize: function() {
      this.stickit();
    }
  });

  Indigo.DocumentView = Backbone.View.extend({
    el: $('body'),
    events: {
      'click .btn.save': 'save',
    },

    initialize: function() {
      var library = new Indigo.Library();

      var document_id = $('[data-document-id]').data('document-id');
      this.document = new Indigo.Document({id: document_id}, {
        collection: library
      });

      new Indigo.DocumentTitleView({model: this.document});
      new Indigo.DocumentPropertiesView({model: this.document});

      this.document.fetch();
    },

    save: function() {
      if (this.document.isValid()) {
        var btn = this.$el.find('.btn.save');

        btn.prop('disabled', true);

        this.document
          .save()
          .always(function() {
            btn.prop('disabled', false);
          });
      }
    },
  });
})(window);
