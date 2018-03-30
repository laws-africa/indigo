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
    workExpressionsTemplate: '#work-expressions-template',
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
      this.dirty = false;

      this.workExpressionsTemplate = Handlebars.compile($(this.workExpressionsTemplate).html());
      this.model = new Indigo.Work(Indigo.Preloads.work);
      this.model.expressionSet = Indigo.library.expressionSet(this.model);

      this.listenTo(this.model, 'change:country', this.updatePublicationOptions);
      this.listenTo(this.model, 'change:title', this.updatePageTitle);
      this.listenTo(this.model, 'change', this.setDirty);
      this.listenTo(this.model, 'change:frbr_uri', _.debounce(_.bind(this.renderExpressions, this), 500));
      this.updatePublicationOptions();

      this.listenTo(this.model, 'sync', this.setClean);
      this.listenTo(this.model, 'change', this.canSave);

      // prevent the user from navigating away without saving changes
      $(window).on('beforeunload', _.bind(this.windowUnloading, this));

      this.model.updateFrbrUri();
      this.stickit();
      this.renderExpressions();
      this.canSave();
    },

    updatePageTitle: function() {
      document.title = this.model.get('title') + ' - Indigo';
      if (!this.model.isNew()) $('.workspace-header h4').text(this.model.get('title'));
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

    renderExpressions: function() {
      if (this.model.isNew()) return;

      var self = this;
      var documents = new Indigo.Library(),
          frbr_uri = this.model.get('frbr_uri');

      // only load documents with this frbr_uri
      documents.url = documents.url + '?frbr_uri' + encodeURIComponent(frbr_uri);
      documents.fetch().done(function() {
        var expressionSet = new Indigo.ExpressionSet(null, {
          library: documents,
          frbr_uri: frbr_uri,
        });

        var dates = expressionSet.allDates(),
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

        self.$('.work-expressions').html(self.workExpressionsTemplate({
          expressions: expressions,
          work: self.model.toJSON(),
        }));
      });
    },

    windowUnloading: function(e) {
      if (this.dirty) {
        e.preventDefault();
        return 'You will lose your changes!';
      }
    },
  });
})(window);
