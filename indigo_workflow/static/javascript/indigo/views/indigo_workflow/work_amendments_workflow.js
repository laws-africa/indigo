(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * This view injects additional logic into the Work Amendments view
   * to handling creating new amendment workflows.
   */
  Indigo.WorkAmendmentsWorkflowView = Backbone.View.extend({
    el: '#work-amendments-view',
    events: {
      'show.bs.modal #new-create-pit-workflow-modal': 'onShowModal',
    },

    initialize: function() {
      var self = this;
      // override the render method of the primary work amendments view so that
      // we can inject additional logic
      var originalRender = Indigo.view.render;

      function adjustedRender() {
        var result = originalRender.apply(this, arguments);

        // insert our logic
        // TODO: perms
        var btn = document.createElement('button');
        btn.setAttribute('class', 'btn btn-outline-secondary');
        btn.setAttribute('data-toggle', 'modal');
        btn.setAttribute('data-target', '#new-create-pit-workflow-modal');
        btn.innerHTML = '<i class="fa fa-tasks"></i> Create workflow';

        Indigo.view.$('.timeline-item .card-footer').prepend(btn);

        return result;
      }

      Indigo.view.render = adjustedRender;
    },

    onShowModal: function(e) {
      var btn = e.relatedTarget,
          $item = $(btn).closest('.timeline-item'),
          date = $item.data('date'),
          index = $item.data('index'),
          amendment = Indigo.view.collection.at(index),
          $form = $(e.target).find('form');


      $form.find('[name=date]').val(date);
      $form.find('[name=amendment]').val(amendment ? amendment.get('id') : '');
    },
  });
})(window);
