(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handle the defined terms view.
   */
  Indigo.DocumentDefinedTermsView = Backbone.View.extend({
    el: '#defined-terms-modal',
    termsTemplate: '#terms-template',
    events: {
      'click .link-terms': 'linkTerms',
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
      var terms = {};

      return _.map(this.model.xmlDocument.querySelectorAll('def'), function(elem) {
        return elem.textContent;
      }).sort();
    },

    linkTerms: function(e) {
      var self = this,
          $btn = this.$el.find('.link-terms'),
          data = {};

      data.document = this.model.document.toJSON();
      data.document.content = this.model.toXml();

      $btn
        .prop('disabled', true)
        .find('.fa').addClass('fa-spin');

      $.ajax({
        url: '/api/analysis/link-terms',
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"})
        .then(function(response) {
          self.model.set('content', response.document.content);
        })
        .always(function() {
          $btn
            .prop('disabled', false)
            .find('.fa').removeClass('fa-spin');
        });
    },
  });
})(window);
