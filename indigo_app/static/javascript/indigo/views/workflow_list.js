(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * A view for listing workflows.
   */
  Indigo.WorkflowListView = Backbone.View.extend({
    el: 'body',
    events: {
      'change #workflow-filter-form': 'formChanged',
    },

    formChanged: function(e) {
      e.currentTarget.submit();
    },
  });
})(window);
