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
        var target = JSON.parse(container.getAttribute('data-highlight')),
            range = window.indigoAkn.targetToRange(target, container);

        if (range) {
          window.indigoAkn.markRange(range, 'mark', function(m) {
            m.classList.add('active');
            return m;
          });
        }
      });
    },
  });
})(window);
