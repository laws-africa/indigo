(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handle the work amendments display.
   */
  Indigo.WorkAmendmentsView = Backbone.View.extend({
    el: '#work-amendments-view',
    events: {
      'click .add-amendment': 'addAmendment',
    },

    initialize: function() {
      this.model = new Indigo.Work(Indigo.Preloads.work);
    },

    addAmendment: function(e) {
      e.preventDefault();

      var chooser = new Indigo.WorkChooserView({country: this.model.get('country')}),
          form = document.getElementById('new-amendment-form'),
          self = this;

      chooser.showModal().done(function(chosen) {
        if (chosen) {
          form.elements.date.value = chosen.get('commencement_date') || chosen.get('publication_date');
          form.elements.amending_work.value = chosen.get('id');
          form.submit();
        }
      });
    },
  });
})(window);
