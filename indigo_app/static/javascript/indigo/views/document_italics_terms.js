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
      var terms = {};

      return _.unique(_.map(this.model.xmlDocument.querySelectorAll('i'), function(elem) {
        return elem.textContent;
      }).sort());
    },

    markUpItalics: function(e) {
      var self = this,
          $btn = this.$el.find('.mark-up-italics'),
          data = {'document': this.model.document.toJSON()};

      let content = this.model.toXml();
      if (Indigo.Preloads.provisionEid) {
        content = `<akomaNtoso xmlns="${this.model.xmlDocument.firstChild.getAttribute('xmlns')}">${content}</akomaNtoso>`;
        data.document.provision_eid = Indigo.Preloads.provisionEid;
      }
      data.document.content = content;

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
      // remove all italics mark-up
      let changed = false;

      // TODO: navigate to 'In this document' first (this click() doesn't do anything)
      this.$('a[href="#this-document-italics-terms"]').click();

      this.model.xmlDocument.querySelectorAll('i').forEach(function(term) {
        // get rid of <i>
        var parent = term.parentNode;
        while (term.firstChild) parent.insertBefore(term.firstChild, term);
        parent.removeChild(term);

        changed = true;
      });

      if (changed) {
        this.model.trigger('change:dom');
      }
    }
  });
})(window);
