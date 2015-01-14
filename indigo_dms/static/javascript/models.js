(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.Document = Backbone.Model.extend({
    defaults: {
      draft: true,
      title: '(none)',
    }
  });

  Indigo.Library = Backbone.Collection.extend({
    model: Document,
    url: '/api/documents'
  });
})(window);
