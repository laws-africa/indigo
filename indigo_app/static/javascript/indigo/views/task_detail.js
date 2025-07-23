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
      window.addEventListener('htmx:afterRequest', () => {
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
      })
    },

    commentChanged: function(e) {
      var text = (e.target.value || '').trim();
      this.$('#task-comment-form #id_submit').attr('disabled', text.length === 0);

      if (text.length > 0) {
        this.$('#btn_request_changes').val($t('Comment and request changes'));
        this.$('#btn_approve').val($t('Comment and approve'));
        this.$('#btn_reopen').val($t('Comment and reopen'));
        this.$('#btn_finish').val($t('Comment and finish'));
        this.$('#btn_submit_for_review').val($t('Comment and submit for review'));

      } else {
        this.$('#btn_request_changes').val($t('Request changes'));
        this.$('#btn_approve').val($t('Approve'));
        this.$('#btn_reopen').val($t('Reopen'));
        this.$('#btn_finish').val($t('Finish'));
        this.$('#btn_submit_for_review').val($t('Submit for review'));
      }
    },
  });
})(window);
