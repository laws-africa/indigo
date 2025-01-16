(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handle the references view.
   */
  Indigo.DocumentReferencesView = Backbone.View.extend({
    el: '#references-modal',
    template: '#references-template',
    events: {
      'click .find-references': 'findReferences',
      'click .remove-references': 'removeReferences',
    },

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());
      // TODO: do this on modal popup?
      this.model.on('change change:dom', this.render, this);
    },

    render: function() {
      var references = this.listReferences();
      this.$el.find('.document-references-list').html(this.template({references: references}));
    },

    /** Find references in this document */
    listReferences: function() {
      var refs = {};

      refs = this.model.xmlDocument.querySelectorAll('ref');
      refs = _.filter(refs, function(elem) {
        var h = elem.getAttribute('href');
        return h && (h.startsWith('/') || h.startsWith('#'));
      });

      refs = _.unique(_.map(refs, function(elem) {
        return {
          'href': elem.getAttribute('href'),
          'url': Indigo.resolverUrl + elem.getAttribute('href'),
          'title': elem.textContent,
        };
      }), function(ref) {
        // unique on this string
        return ref.href + "|" + ref.title;
      });

      return _.sortBy(refs, 'url');
    },

    findReferences: function(e) {
      let self = this,
          $btn = this.$el.find('.find-references');

      if (!Indigo.view.sourceEditorView.confirmAndDiscardChanges()) return;

      const data = this.model.toSimplifiedJSON();

      $btn
        .prop('disabled', true)
        .find('i').addClass('fa-spin');

      $.ajax({
        url: this.model.document.url() + '/analysis/link-references',
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"})
        .then(function(response) {
          self.model.set('content', response.xml);
        })
        .always(function() {
          $btn
            .prop('disabled', false)
            .find('i').removeClass('fa-spin');
        });
    },

    removeReferences: function(e) {
      if (!Indigo.view.sourceEditorView.confirmAndDiscardChanges()) return;
      let xml = this.model.xmlDocument.cloneNode(true);

      // remove all non-absolute refs
      xml.querySelectorAll('ref').forEach(function(ref) {
        if ((ref.getAttribute('href') || "").startsWith('/') || (ref.getAttribute('href') || "").startsWith('#')) {
          // get rid of ref
          const parent = ref.parentNode;
          while (ref.firstChild) parent.insertBefore(ref.firstChild, ref);
          parent.removeChild(ref);
        }
      });

      // set the content once for one mutation record
      this.model.set('content', Indigo.toXml(xml));
    },
  });
})(window);
