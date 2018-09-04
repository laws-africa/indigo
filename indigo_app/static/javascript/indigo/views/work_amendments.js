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
      'click .create-expression': 'createExpression',
    },

    initialize: function() {
      this.model = new Indigo.Work(Indigo.Preloads.work);
    },

    addAmendment: function(e) {
      e.preventDefault();

      var chooser = new Indigo.WorkChooserView({}),
          form = document.getElementById('new-amendment-form'),
          self = this;

      chooser.setFilters({country: this.model.get('country')});
      chooser.showModal().done(function(chosen) {
        if (chosen) {
          form.elements.date.value = chosen.get('commencement_date') || chosen.get('publication_date');
          form.elements.amending_work.value = chosen.get('id');
          form.submit();
        }
      });
    },

    createExpression: function(e) {
      e.preventDefault();

      // create an amended version of this document at a particular date
      var date = $(e.target).closest('.timeline-item').data('date');

      if (confirm('Create a new amended versiot at ' + date + '? Unsaved changes will be lost!')) {
        Indigo.progressView.peg();

        $.post(this.model.url() + '/expressions_at?date=' + date)
          .done(function(doc) {
            document.location = '/documents/' + doc.id + '/';
          })
          .fail(function() {
            Indigo.progressView.unpeg();
          });
      }
    },
  });
})(window);
