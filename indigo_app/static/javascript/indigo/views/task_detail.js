(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * A view for the task detail page.
   */
  Indigo.TaskDetailView = Backbone.View.extend({
    el: '.page-body',
    events: {
      'change #id_comment': 'commentChanged',
      'keyup #id_comment': 'commentChanged',
    },

    initialize: function() {
      this.$('[data-highlight]').each(function(i, container) {
        var target = container.getAttribute('data-highlight');
        var elem = container.querySelector("[data-id='" + target + "']");
        if (elem) elem.classList.add('highlight');
      });
    },

    commentChanged: function(e) {
      var text = (e.target.value || '').trim();
      this.$('#task-comment-form #id_submit').attr('disabled', text.length == 0);
    }
  });
})(window);
