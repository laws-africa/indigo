(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // django doesn't link blank date fields, send null instead
  function emptyIsNull(val) {
    return (!val || val.trim() === "") ? null : val;
  }

  // Handle the document properties form, and saving them back to the server.
  Indigo.DocumentPropertiesView = Backbone.View.extend({
    el: '.document-properties-view',
    bindings: {
      '#document_title': 'title',
      '#document_expression_date': {
        observe: 'expression_date',
        onSet: emptyIsNull,
      },
      '#document_language': 'language',
    },

    initialize: function() {
      this.amendments = new Indigo.WorkAmendmentCollection(Indigo.Preloads.amendments, {
        work: this.model,
      });

      this.listenTo(this.model, 'change:draft change:frbr_uri change:language change:expression_date sync', this.showPublishedUrl);
      this.stickit();
      this.render();
    },

    showPublishedUrl: function() {
      var url = this.model.manifestationUrl();

      this.$el.find('.published-url').toggle(!this.model.get('draft'));
      this.$el.find('#document_published_url').attr('href', url).text(url);
    },

    render: function() {
      var work = this.model.work;

      this.$('.document-work-title')
        .text(work.get('title'))
        .attr('href', '/works' + work.get('frbr_uri'));
    },
  });
})(window);
