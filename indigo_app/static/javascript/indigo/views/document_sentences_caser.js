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
      let self = this,
          data = {'document': this.model.document.toJSON()};

      data.document.content = this.model.toXml();

      $.ajax({
        url: this.model.document.url() + '/analysis/sentence-case-headings',
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"})
          .then(function(response) {
            self.model.set('content', response.document.content);
          });
    },
  });
})(window);
