(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Compare different expressions (in the same language) of a work.
   */
  Indigo.DocumentComparisonsView = Backbone.View.extend({
    el: '.document-comparisons-view',
    template: '#comparisons-template',
    events: {
      'click .dismiss': 'dismiss'
    },

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());

      this.expressions = options.expressions;
      this.documentContent = options.documentContent;

      $('.menu .comparisons').on('click', _.bind(this.show, this));

    },

    show: function(e) {
      e.preventDefault();
      $('.work-view').addClass('d-none');
      this.$el.removeClass('d-none');
      this.$el.find('.comparison-container').html(this.template({
        expressions: this.expressions
      }))

    }

  });
})(window);
