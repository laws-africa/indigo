(function(exports) {
  "use strict";

  var DocumentTitleView = Backbone.View.extend({
    el: $('.workspace-header'),
    bindings: {
      'h4': 'title'
    },

    initialize: function() {
      this.stickit();
    },
  });

  var DocumentPropertiesView = Backbone.View.extend({
    el: $('#props-tab article'),
    bindings: {
      '#document_title': 'title',
    },

    initialize: function() {
      this.stickit();
    }
  });

  var DocumentView = Backbone.View.extend({
    el: $('body'),
    events: {
    },

    initialize: function() {
      var library = new Library();

      var document_id = $('[data-document-id]').data('document-id');
      this.document = new Document({id: document_id}, {
        collection: library
      });

      new DocumentTitleView({model: this.document});
      new DocumentPropertiesView({model: this.document});

      this.document.fetch();
    },
  });

  exports.DocumentView = DocumentView;
})(window);
