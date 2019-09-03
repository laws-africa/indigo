(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Compare different expressions (in the same language) of a work.
   */
  Indigo.DocumentComparisonView = Backbone.View.extend({
    el: '.document-comparison-view',
    events: {
      'click .dismiss': 'dismiss'
    },

    initialize: function(options) {
      this.documentContent = options.documentContent;

      $('.menu .comparison').on('click', _.bind(this.show, this));

    },

    comparison: function(comparison_doc_id) {

      var data = {},
          self = this;
      data.document = this.documentContent.document.toJSON();
      data.document.content = this.documentContent.toXml();
      data.comparison_doc_id = comparison_doc_id;

      $.ajax({
        url: '/api/document-comparison',
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"})
          .then(function(response) {
            self.$el.find('.akoma-ntoso').html(response.content);
            self.$el.find('.n_changes').html(response.n_changes);
            self.$el.find('.comp_doc_date').html(response.comp_doc_date);
          });

    },

    show: function(e) {
      var comparison_doc_id = e.currentTarget.id;
      e.preventDefault();
      $('.work-view').addClass('d-none');
      this.$el.removeClass('d-none');
      this.comparison(comparison_doc_id);

    },

    dismiss: function(e) {
      e.preventDefault();
      this.$el.addClass('d-none');
      $('.work-view').removeClass('d-none');
    }

  });
})(window);
