(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * A view for listing tasks.
   */
  Indigo.TaskListView = Backbone.View.extend({
    el: 'body',
    events: {
      'change #task-filter-form': 'formChanged',
    },

    formChanged: function(e) {
      e.currentTarget.submit();
    },
  });
})(window);
