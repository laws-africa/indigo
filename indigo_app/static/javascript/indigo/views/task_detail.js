(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * A view for the task detail page.
   */
  Indigo.TaskDetailView = Backbone.View.extend({
    el: '.page-body',

    initialize: function() {
      this.$('[data-highlight]').each(function(i, container) {
        var target = container.getAttribute('data-highlight');
        var elem = container.querySelector("[data-id='" + target + "']");
        if (elem) elem.classList.add('highlight');
      });
    },
  });
})(window);
