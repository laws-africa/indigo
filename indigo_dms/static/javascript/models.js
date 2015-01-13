(function(exports) {
  "use strict";

  var Document = Backbone.Model.extend({
    defaults: {
      draft: true,
      title: '(none)',
    }
  });

  var Library = Backbone.Collection.extend({
    model: Document,
    url: '/api/documents'
  });

  exports.Document = Document;
  exports.Library = Library;
})(window);
