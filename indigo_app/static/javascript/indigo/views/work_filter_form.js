(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /** This view handles the work filter form.
   */
  Indigo.WorkFilterFormView = Backbone.View.extend({
    el: '#work-filter-form',
    events: {
      'change [data-toggle="daterange"]': 'dateRangeToggled',
    },

    dateRangeToggled: function(e) {
      // When value of the toggler is 'range' reveal the date range elements
      var input = e.currentTarget;

      this.$('#' + input.name + '-daterange').toggleClass('d-none', input.value != 'range');
    },
  });
})(window);
