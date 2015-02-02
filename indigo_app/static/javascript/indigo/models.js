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
