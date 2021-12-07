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

    taskSelected: function(e) {
      var ids = _.map(document.querySelectorAll('input[type=checkbox][name=tasks]:checked'), function(e) { return e.value; });
      this.model.set('tasks', ids);

      $(e.target)
        .closest('.card-body')
        .toggleClass('bg-selected', e.checked);
    },

    updateFormOptions: function() {
      // show the form?
      if (this.model.get('tasks').length > 0) {
        this.$form.siblings().addClass('d-none');
        this.$form.removeClass('d-none');
      } else {
        this.$form.siblings().removeClass('d-none');
        this.$form.addClass('d-none');
      }

      const formData = this.$form.serialize() + '&unassign';
      $.post(this.$form.data('assignees-url'), formData)
        .then((resp) => {
          const html = $.parseHTML(resp.trim())[0];
          const $menu = this.$form.find('.dropdown-menu');
          $menu.empty();
          $menu.append(html.children);
        });
    },
  });
})(window);
