(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.TaskBulkUpdateView = Backbone.View.extend({
    el: '.page-body',
    events: {
      'change input[type=checkbox][name=tasks]': 'taskSelected',
    },

    initialize: function() {
      this.$form = this.$('#bulk-task-update-form');
      this.model = new Backbone.Model({'tasks': []});
      this.listenTo(this.model, 'change', this.updateFormOptions);
    },

    taskSelected: function() {
      var ids = _.map(document.querySelectorAll('input[type=checkbox][name=tasks]:checked'), function(e) { return e.value; });
      this.model.set('tasks', ids);
    },

    updateFormOptions: function() {
      // assigned user options is the intersection of the assignment options for all tasks
      var options = null,
          names = {};

      // show the form?
      if (this.model.get('tasks').length > 0) {
        this.$form.siblings().addClass('d-none');
        this.$form.removeClass('d-none');
      } else {
        this.$form.siblings().removeClass('d-none');
        this.$form.addClass('d-none');
      }

      this.model.get('tasks').forEach(function(id) {
        var $buttons = $("#task-" + id + " .assign-task-form .dropdown-item[value]"),
            taskOptions = _.map($buttons, function(b) {
              names[b.value] = b.textContent;
              return b.value;
            });

        if (taskOptions.length > 0) {
          if (options === null) {
            options = taskOptions;
          } else {
            options = _.intersection(options, taskOptions);
          }
        }
      });

      if (options) {
        var $select = this.$form.find('[name=assigned_to]');
        $select.empty();
        options.forEach(function (value) {
          var option = document.createElement('option');
          option.value = value;
          option.innerText = names[value];
          $select.append(option);
        });
      }
    },
  });

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
      new Indigo.TaskBulkUpdateView();
    },
  });
})(window);
