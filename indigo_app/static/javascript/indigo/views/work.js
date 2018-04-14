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
      'click .change-repeal': 'changeRepeal',
      'click .delete-repeal': 'deleteRepeal',
    },
    workExpressionsTemplate: '#work-expressions-template',
    workRepealTemplate: '#work-repeal-template',
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
      '#work_repealed_date': {
        observe: 'repealed_date',
        onSet: emptyIsNull,
      },
    },

    initialize: function(options) {
      this.dirty = false;

      this.workExpressionsTemplate = Handlebars.compile($(this.workExpressionsTemplate).html());
      this.workRepealTemplate = Handlebars.compile($(this.workRepealTemplate).html());

      this.model = new Indigo.Work(Indigo.Preloads.work);
      this.listenTo(this.model, 'change:country', this.updatePublicationOptions);
      this.listenTo(this.model, 'change:country change:locality', this.updateBreadcrumb);
      this.listenTo(this.model, 'change:title change:frbr_uri', this.updatePageTitle);
      this.listenTo(this.model, 'change', this.setDirty);
      this.listenTo(this.model, 'change:frbr_uri', _.debounce(_.bind(this.refreshExpressions, this), 500));

      this.filteredLibrary = new Indigo.Library({country: null});
      this.model.expressionSet = this.filteredLibrary.expressionSet(this.model);
      this.listenTo(this.model.expressionSet, 'change reset', this.renderExpressions);

      this.listenTo(this.model, 'sync', this.setClean);
      this.listenTo(this.model, 'change', this.canSave);
      this.listenTo(this.model, 'change:repealed_by', this.repealChanged);

      // prevent the user from navigating away without saving changes
      $(window).on('beforeunload', _.bind(this.windowUnloading, this));

      this.model.updateFrbrUri();
      this.updatePublicationOptions();
      this.stickit();
      this.refreshExpressions();
      this.repealChanged();
      this.canSave();
    },

    updatePageTitle: function() {
      document.title = this.model.get('title') + ' - Indigo';
      if (!this.model.isNew()) $('.workspace-header h4, .work-title').text(this.model.get('title'));
      this.$('.work-frbr-uri').text(this.model.get('frbr_uri'));
    },

    setDirty: function() {
      this.dirty = true;
      this.canSave();
    },

    setClean: function() {
      this.dirty = false;
      this.canSave();
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

    updateBreadcrumb: function() {
      var country = Indigo.countries[this.model.get('country')],
          locality = this.model.get('locality');

      this.$('.work-country').text(country.name);
      this.$('.work-locality').text(locality ? country.localities[locality] + ' (' + locality + ')' : '');
    },

    canSave: function() {
      this.$('.btn.save').attr('disabled', !this.dirty || !this.model.isValid());
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

    refreshExpressions: function() {
      // only load documents with this frbr_uri
      this.filteredLibrary.setParams({frbr_uri: this.model.get('frbr_uri')});
    },

    renderExpressions: function() {
      if (this.model.isNew()) return;

      var expressionSet = this.model.expressionSet,
          dates = expressionSet.allDates(),
          pubDate = expressionSet.initialPublicationDate();

      // build up a view of expressions for this work
      var expressions = _.map(dates, function(date) {
        var doc = expressionSet.atDate(date);
        var info = {
          date: date,
          document: doc && doc.toJSON(),
          amendments: _.map(expressionSet.amendmentsAtDate(date), function(a) { return a.toJSON(); }),
          initial: date == pubDate,
        };
        info.linkable = info.document;

        return info;
      });

      this.$('.work-expressions').html(this.workExpressionsTemplate({
        expressions: expressions,
        work: this.model.toJSON(),
      }));
    },

    deleteRepeal: function() {
      this.model.set('repealed_by', null);
    },

    changeRepeal: function() {
      var chooser = new Indigo.WorkChooserView({}),
          self = this;

      if (this.model.get('repealed_by')) {
        chooser.choose(Indigo.works.get(this.model.get('repealed_by')));
      }
      chooser.setFilters({country: this.model.get('country')});
      chooser.showModal().done(function(chosen) {
        if (chosen) {
          self.model.set('repealed_by', chosen.get('id'));
          self.model.set('repealed_date', chosen.get('publication_date'));
        }
      });
    },

    repealChanged: function() {
      var repeal,
          self = this,
          repealed_by = this.model.get('repealed_by');

      if (repealed_by) {
        repealed_by = new Indigo.Work({id: repealed_by});
        repealed_by.fetch().done(function() {
          self.$el.addClass('is-repealed');
          self.$('.work-repeal-view').html(self.workRepealTemplate({
            repealed_by: repealed_by.toJSON(),
          }));
        });

      } else {
        this.$el.removeClass('is-repealed');
        this.$('.work-repeal-view').html(this.workRepealTemplate({}));
      }
    },

    windowUnloading: function(e) {
      if (this.dirty) {
        e.preventDefault();
        return 'You will lose your changes!';
      }
    },
  });
})(window);
