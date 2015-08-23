(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handle the document analysis view.
   */
  Indigo.DocumentAnalysisView = Backbone.View.extend({
    el: '.document-analysis-view',
    termsTemplate: '#terms-template',
    events: {
      'click .link-definitions': 'linkDefinitions',
    },

    initialize: function(options) {
      this.termsTemplate = Handlebars.compile($(this.termsTemplate).html());
      this.model.on('change', this.render, this);
    },

    render: function() {
      var terms = this.findTerms();

      this.$el.find('.document-terms-list').html(this.termsTemplate({terms: terms}));
    },

    /** Find defined terms in this document */
    findTerms: function() {
      return _.map(this.model.xmlDocument.querySelectorAll('meta TLCTerm'), function(elem) {
        return elem.getAttribute('showAs');
      }).sort();
    },

    linkDefinitions: function(e) {
      // TODO
    },
  });
})(window);
