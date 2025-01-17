(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handle the sentence caser view.
   */
  Indigo.DocumentSentenceCaseView = Backbone.View.extend({
    el: '#sentence-caser',
    events: {
      'click .sentence-case-headings': 'sentenceCaseHeadings'
    },

    sentenceCaseHeadings: function(e) {
      let self = this;

      if (!Indigo.view.sourceEditorView.confirmAndDiscardChanges()) return;

      const data = this.model.toSimplifiedJSON();

      $.ajax({
        url: this.model.document.url() + '/analysis/sentence-case-headings',
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"})
          .then(function(response) {
            self.model.set('content', response.xml);
          });
    },
  });
})(window);
