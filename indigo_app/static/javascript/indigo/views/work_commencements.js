(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handle the work commencements display.
   */
  Indigo.WorkCommencementsView = Backbone.View.extend({
    el: '#work-commencements-view',
    events: {
      'click .add-commencement': 'addCommencement',
    },

    initialize: function() {
      this.model = new Indigo.Work(Indigo.Preloads.work);
      this.$('.commencement-form').on('show.bs.collapse', _.bind(this.formShow, this));
      this.$('.commencement-form').on('hide.bs.collapse', _.bind(this.formHide, this));
    },

    addCommencement: function(e) {
      e.preventDefault();

      var chooser = new Indigo.WorkChooserView({
            country: this.model.get('country'),
            locality: this.model.get('locality') || "-",
          }),
          form = document.getElementById('new-commencement-form'),
          self = this;

      chooser.showModal().done(function(chosen) {
        if (chosen) {
          form.elements.date.value = chosen.get('commencement_date') || chosen.get('publication_date');
          form.elements.commencing_work.value = chosen.get('id');
          form.submit();
        }
      });
    },

    formShow: function(e) {
      // hide the details
      e.target.parentElement.querySelector('.commencement-details').classList.remove('show');
    },

    formHide: function(e) {
      // show the details
      e.target.parentElement.querySelector('.commencement-details').classList.add('show');
    },
  });
})(window);
