(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.BatchAddWorkView = Backbone.View.extend({
    el: '#bulk-import-works-view',

    events: {
      'click .btn.show-progress': 'showProgress',
    },

    showProgress: function(e) {
      document.getElementById('import-progress').classList.remove('d-none');
    },
  });
})(window);
