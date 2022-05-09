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
      'click .remove-terms': 'removeTerms',
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
        .find('i').addClass('fa-spin');

      $.ajax({
        url: this.model.document.url() + '/analysis/link-terms',
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
            .find('i').removeClass('fa-spin');
        });
    },

    removeTerms: function(e) {
      var changed = false;

      // unwrap all <def>s
      this.model.xmlDocument.querySelectorAll('def').forEach(function(def) {
        var parent = def.parentNode;
        while (def.firstChild) parent.insertBefore(def.firstChild, def);
        parent.removeChild(def);

        changed = true;
      });

      // unwrap all <term>s
      this.model.xmlDocument.querySelectorAll('term').forEach(function(term) {
        var parent = term.parentNode;
        while (term.firstChild) parent.insertBefore(term.firstChild, term);
        parent.removeChild(term);
      });

      // remove all <TLCTerm>s
      this.model.xmlDocument.querySelectorAll('TLCTerm').forEach(function(tlcTerm) {
        var parent = tlcTerm.parentNode;
        parent.removeChild(tlcTerm);
      });

      // remove all refersTo attributes that start with '#term-'
      this.model.xmlDocument.querySelectorAll('[refersTo]').forEach(function(el) {
        if ((el.getAttribute('refersTo') || '').startsWith('#term-')) {
          el.removeAttribute('refersTo');
        }
      });

      if (changed) this.model.trigger('change:dom');
    },
  });
})(window);
