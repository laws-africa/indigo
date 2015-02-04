(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // The document body could be huge, so the API handles it outside
  // of the document data. We model this with a separate wraps the document's body, available at /documents/1/body
  Indigo.DocumentBody = Backbone.Model.extend({
  });

  Indigo.Document = Backbone.Model.extend({
    defaults: {
      draft: true,
      title: '(none)',
    },

    initialize: function() {
      this.body = new Indigo.DocumentBody();
      this.body.url = this.url() + '/body';
    },
  });

  Indigo.Library = Backbone.Collection.extend({
    model: Indigo.Document,
    url: '/api/documents'
  });

  Indigo.User = Backbone.Model.extend({
    url: '/auth/user',

    authenticated: function() {
      return !!this.get('username');
    },
  });
})(window);
