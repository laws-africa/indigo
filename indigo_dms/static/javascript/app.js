$(function() {
  "use strict";

  var Document = Backbone.Model.extend({
    defaults: {
      draft: true,
    }
  });

  var Library = Backbone.Collection.extend({
    model: Document,
    url: '/api/documents'
  });

  var DocumentTitleView = Backbone.View.extend({
    el: $('.workspace-header'),
    template: _.template('<h4><%= title %></h4>'),

    initialize: function() {
      this.listenTo(this.model, 'change', this.render);
    },

    render: function() {
      this.$el.html(this.template(this.model.toJSON()));
      return this;
    },
    
  });

  var DocumentView = Backbone.View.extend({
    el: $('body'),
    events: {
    },

    initialize: function() {
      var library = new Library();

      this.document = new Document({
        id: $('[data-document-id]').data('document-id'),
      }, {
        collection: library
      });

      new DocumentTitleView({model: this.document});

      this.document.fetch();
    },

    foo: function() {
      console.log(this.document.get('id'));
    }
  });

  var app = new DocumentView();
  window.app = app;

  app.document.set('title', 'foo');
});
