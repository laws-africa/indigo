(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * This view handles the basic StartPlaceWorkflowView
   * logic.
   */
  Indigo.StartPlaceWorkflowView = Backbone.View.extend({
    el: '#new-workflow-form',
    events: {
      'change #id_country': 'countryChanged',
    },

    initialize: function() {
      this.countryChanged();
    },

    countryChanged: function() {
      // update the locality list to match the country
      var selected = this.$('#id_country')[0].selectedOptions[0],
          country = Indigo.countries[selected.getAttribute('data-code')],
          localities = country.localities || [],
          $list = this.$('#id_locality');

      $list.empty();
      var none = document.createElement('option');
      none.innerText = '(none)';
      $list.append(none);

      _.each(localities, function(name, code) {
        var sel = document.createElement('option');
        sel.setAttribute('value', code);
        sel.innerText = name;
        $list.append(sel);
      });
    },
  });
})(window);
