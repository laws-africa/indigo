(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Compare different expressions (in the same language) of a work.
   */
  Indigo.DocumentComparisonView = Backbone.View.extend({
    el: '.document-comparison-view',
    comparisonHeaderTemplate: '#comparison-header-template',
    events: {
      'click .dismiss': 'dismiss'
    },

    initialize: function(options) {
      this.comparisonHeaderTemplate = Handlebars.compile($(this.comparisonHeaderTemplate).html());
      this.document = options.document;
      this.documentContent = options.documentContent;
      this.expressions = new Indigo.Library(Indigo.Preloads.expressions);

      $('.show-pit-comparison').on('click', _.bind(this.show, this));
    },

    comparison: function(comparisonDocId) {
      var data = {},
          self = this;
      data.document = this.documentContent.document.toJSON();
      data.document.content = this.documentContent.toXml();
      data.comparison_doc_id = comparisonDocId;
      this.comparisonDoc = this.expressions.get(comparisonDocId);

      $.ajax({
        url: '/api/document-comparison',
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"})
          .then(function(response) {
            self.$el.find('.akoma-ntoso').html(response.content);
            self.$el.find('.n_changes').html(response.n_changes);
          });
    },

    show: function(e) {
      var comparisonDocId = e.currentTarget.id;
      e.preventDefault();
      $('.work-view').addClass('d-none');
      this.$el.removeClass('d-none');
      this.comparison(comparisonDocId);

      this.$('.title').html(this.comparisonHeaderTemplate({
        document: this.document.toJSON(),
        comparison_doc: this.comparisonDoc.toJSON()
      }));
    },

    dismiss: function(e) {
      e.preventDefault();
      this.$el.addClass('d-none');
      $('.work-view').removeClass('d-none');
    }

  });
})(window);
