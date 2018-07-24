(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * This view injects additional logic into the Work Amendments view
   * to handling creating new amendment workflows.
   */
  Indigo.WorkAmendmentsWorkflowView = Backbone.View.extend({
    initialize: function() {
      alert('hi');
    },
  });
})(window);
