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
        var target = JSON.parse(container.getAttribute('data-highlight')),
            range = Indigo.dom.targetToRange(target, container);

        if (range) {
          Indigo.dom.markRange(range, 'mark', function(m) {
            m.classList.add('active');
          });
        }
      });
    },

    commentChanged: function(e) {
      var text = (e.target.value || '').trim();
      this.$('#task-comment-form #id_submit').attr('disabled', text.length === 0);

      if (text.length > 0) {
        this.$('#btn_request_changes').val('Comment and Request Changes');
        this.$('#btn_approve').val('Comment and Approve');
        this.$('#btn_reopen').val('Comment and Reopen');
        this.$('#btn_submit_for_review').val('Comment and Submit for Review');

      } else {
        this.$('#btn_request_changes').val('Request Changes');
        this.$('#btn_approve').val('Approve');
        this.$('#btn_reopen').val('Reopen');
        this.$('#btn_submit_for_review').val('Submit for Review');
      }
    },
  });
})(window);
