(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * A widget that lists countries and localities and lets the user choose a country, and optionally a locality.
   */
  Indigo.PlaceChooserView = Backbone.View.extend({
    // TODO: add scss (see e.g. work-chooser-box)
    el: '#place-chooser-box',
    template: '#place-chooser-template',
    events: {
      'change .place-chooser-country': 'countryChanged',
      'change .place-chooser-locality': 'localityChanged',
      'click tr': 'itemClicked',
      'hidden.bs.modal': 'dismiss',
      'shown.bs.modal': 'shown',
      'click .btn.choose-place': 'save',
    },

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());
      this.chosenCountry = options.country;
      this.chosenLocality = options.locality;

      this.$el.find('.modal-title').text(options.title);

      this.$el.find('.place-chooser-country').prop('disabled', options.disable_country);
      this.$el.find('.place-chooser-locality').prop('disabled', options.disable_locality);

      this.updateLocalities();
    },

    /**
     * Show the chooser as a modal dialog, and return a deferred that will be resolved
     * with the chosen item (or null).
     */
    showModal: function() {
      this.deferred = $.Deferred();
      this.$el.modal('show');
      return this.deferred;
    },

    countryChanged: function(e) {
      this.chosenCountry = e.target.selectedOptions[0].value;
      this.chosenLocality = null;
      this.updateLocalities();
    },

    localityChanged: function(e) {
      this.chosenLocality = e.target.selectedOptions[0].value;
    },

    updateLocalities: function() {
      var country = this.chosenCountry,
          locality = this.chosenLocality,
          localities = _.clone(Indigo.countries[country].localities);
      var $select = this.$('select.place-chooser-locality')
        .empty()
        .toggle(!_.isEmpty(localities));

      localities = _.map(localities, function(name, code) {
        return {
          name: name,
          code: code,
        };
      });
      localities.push({
        name: '(none)',
        code: '-',
      });
      localities = _.sortBy(localities, function(x) { return x.name.toLocaleLowerCase(); });

      _.each(localities, function(loc) {
        var opt = document.createElement('option');
        opt.setAttribute('value', loc.code);
        opt.innerText = loc.name;
        opt.selected = loc.code === locality;
        $select.append(opt);
      });
    },

    render: function() {
      // ensure selections are up to date
      this.$('select.place-chooser-country option[value="' + this.chosenCountry + '"]').attr('selected', true);
    },

    dismiss: function() {
      this.close();
      this.deferred.reject();
    },

    save: function() {
      this.close();
      this.deferred.resolve(this.chosenCountry);
      this.deferred.resolve(this.chosenLocality);
    },

    close: function() {
      this.stopListening();
      this.$el.modal('hide');
    },
  });

})(window);
