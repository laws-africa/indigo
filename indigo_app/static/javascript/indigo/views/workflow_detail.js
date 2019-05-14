(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.WorkflowAddTasksBox = Backbone.View.extend({
    el: '#workflow-add-tasks-modal',
    events: {
      'click .selectable-task': 'taskClicked',
    },

    taskClicked: function(e) {
      var checkbox = e.currentTarget.querySelector('input[type=checkbox]');

      // check the checkbox?
      if (e.target != checkbox) {
        checkbox.checked = !checkbox.checked;
      }

      e.currentTarget.classList.toggle('list-group-item-primary', checkbox.checked);
    },
  });

  /**
   * A view for the workflow detail page.
   */
  Indigo.WorkflowDetailView = Backbone.View.extend({
    el: '.page-body',

    initialize: function() {
      new Indigo.WorkflowAddTasksBox();
    },
  });
})(window);
