(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handle the references view.
   */
  Indigo.DocumentReferencesView = Backbone.View.extend({
    el: '#references-internal-modal',
    template: '#internal-references-template',
    events: {
      'click .find-section-references': 'findReferences',
      'click .remove-section-references': 'removeReferences'
    },

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());
      // TODO: do this on modal popup?
      this.model.on('change change:dom', this.render, this);
    },

    render: function() {
      var references = this.listReferences();
      this.$el.find('.section-references-list').html(this.template({references: references}));
    },

    /** Find section references in this document */
    listReferences: function() {
      var refs = {};

      refs = this.model.xmlDocument.querySelectorAll('ref');
      refs = _.filter(refs, function(elem) {
        return elem.getAttribute('href') && elem.getAttribute('href').startsWith("#");
      });

      refs = _.unique(_.map(refs, function(elem) {
        return {
          'href': elem.getAttribute('href'),
          'source': elem.textContent
        };
      }));

      return _.sortBy(refs, 'source');
    },

    findReferences: function(e) {
      var self = this,
          $btn = this.$el.find('.find-section-references'),
          data = {'document': this.model.document.toJSON()};

      data.document.content = this.model.toXml();

      $btn
        .prop('disabled', true)
        .find('i').addClass('fa-spin');

      $.ajax({
        url: '/api/analysis/link-section-references',
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"})
        .then(function(response) {
          self.model.set('content', response.document.content);
          // must be a nicer way to automatically trigger this, the entire doc
          // has changed after all
          Indigo.view.tocView.rebuild(true);
        })
        .always(function() {
          $btn
            .prop('disabled', false)
            .find('i').removeClass('fa-spin');
        });
    },

    removeReferences: function(e) {
      // remove all non-absolute refs
      var changed = false;

      this.model.xmlDocument.querySelectorAll('ref').forEach(function(ref) {
        if ((ref.getAttribute('href') || "").startsWith('#')) {
          // get rid of ref
          var parent = ref.parentNode;
          while (ref.firstChild) parent.insertBefore(ref.firstChild, ref);
          parent.removeChild(ref);

          changed = true;
        }
      });

      if (changed) this.model.trigger('change:dom');
    }
  });
})(window);
