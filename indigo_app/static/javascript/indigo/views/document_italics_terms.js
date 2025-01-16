(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handle the italics mark-up view.
   */
  Indigo.DocumentItalicsView = Backbone.View.extend({
    el: '#italics-modal',
    template: '#italics-template',
    events: {
      'click .mark-up-italics': 'markUpItalics',
      'click .remove-italics': 'removeItalics'
    },

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());
      // TODO: do this on modal popup?
      this.model.on('change change:dom', this.render, this);
    },

    render: function() {
      var italics_terms = this.listItalicsTerms();
      this.$el.find('.document-italics-terms').html(this.template({italics_terms: italics_terms}));
    },

    /** Find italics terms in this document */
    listItalicsTerms: function() {
      const terms = new Set();
      for (const term of this.model.xmlDocument.querySelectorAll('i')) {
        terms.add(term.textContent);
      }
      return [...terms].sort();
    },

    markUpItalics: function(e) {
      var self = this,
          $btn = this.$el.find('.mark-up-italics'),
          data = {'document': this.model.document.toJSON()};

      if (!Indigo.view.sourceEditorView.confirmAndDiscardChanges()) return;

      data.document.content = this.model.toXml();

      this.$('a[href="#this-document-italics-terms"]').click();

      $btn
        .prop('disabled', true)
        .find('i').addClass('fa-spin');

      $.ajax({
        url: this.model.document.url() + '/analysis/mark-up-italics',
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

    removeItalics: function(e) {
      if (!Indigo.view.sourceEditorView.confirmAndDiscardChanges()) return;

      // remove all italics mark-up
      this.$('a[href="#this-document-italics-terms"]').click();

      this.model.xmlDocument.querySelectorAll('i').forEach(function(term) {
        // get rid of <i>
        const parent = term.parentNode;
        while (term.firstChild) parent.insertBefore(term.firstChild, term);
        parent.removeChild(term);
      });
    }
  });
})(window);
