(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // django doesn't link blank date fields, send null instead
  function emptyIsNull(val) {
    return (!val || val.trim() === "") ? null : val;
  }

  /**
   * A view that lets a user create or edit a Work.
   */
  Indigo.WorkView = Backbone.View.extend({
    el: '#edit-work-view',
    events: {
      'click .btn.save': 'save',
      'click .btn.delete': 'deleteWork',
    },
    bindings: {
      '#work_country': {
        observe: 'country',
        onSet: function(val) {
          // trigger a redraw of the localities, using this country
          this.country = val;
          this.model.set('locality', null);
          this.model.trigger('change:locality', this.model);
          return val;
        },
      },
      '#work_locality': {
        observe: 'locality',
        selectOptions: {
          collection: function() {
            var country = Indigo.countries[this.country || this.model.get('country')];
            return country ? country.localities : [];
          },
          defaultOption: {label: "(none)", value: null},
        }
      },
      '#work_nature': 'nature',
      '#work_subtype': 'subtype',
      '#work_year': 'year',
      '#work_number': 'number',
      '#work_frbr_uri': 'frbr_uri',
      '#work_title': 'title',
      '#work_publication_date': {
        observe: 'publication_date',
        onSet: emptyIsNull,
      },
      '#work_publication_name': 'publication_name',
      '#work_publication_number': 'publication_number',
      '#work_commencement_date': {
        observe: 'commencement_date',
        onSet: emptyIsNull,
      },
      '#work_assent_date': {
        observe: 'assent_date',
        onSet: emptyIsNull,
      },
    },

    initialize: function(options) {
      this.model = new Indigo.Work(Indigo.Preloads.work);
      this.listenTo(this.model, 'change:country', this.updatePublicationOptions);
      this.listenTo(this.model, 'change:title', this.updatePageTitle);
      this.updatePublicationOptions();

      this.model.updateFrbrUri();
      this.stickit();
    },

    updatePageTitle: function() {
      document.title = this.model.get('title') + ' - Indigo';
    },

    updatePublicationOptions: function() {
      var country = Indigo.countries[this.model.get('country')],
          pubs = (country ? country.publications : []).sort();

      $("#publication_list").empty().append(_.map(pubs, function(pub) {
        var opt = document.createElement("option");
        opt.setAttribute("value", pub);
        return opt;
      }));
    },

    save: function() {
      var self = this,
          isNew = this.model.isNew();

      this.model.save().done(function() {
        if (isNew) {
          // redirect
          Indigo.progressView.peg();
          window.location = '/works/' + self.model.get('id');
        }
      });
    },

    deleteWork: function() {
      if (confirm("Are you sure you want to delete this work?")) {
        this.model.destroy().done(function() {
          window.location = '/';
        });
      }
    },
  });
})(window);
