(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // django doesn't link blank date fields, send null instead
  function emptyIsNull(val) {
    return (!val || val.trim() === "") ? null : val;
  }

  function bool(val) {
    return val == "1";
  }

  // Handle the document properties form, and saving them back to the server.
  Indigo.DocumentPropertiesView = Backbone.View.extend({
    el: '.document-properties-view',
    events: {
      'click .btn-amendments': 'showAmendments',
    },
    bindings: {
      '#document_country': {
        observe: 'country',
        onSet: function(val) {
          // trigger a redraw of the localities, using this country
          this.country = val;
          this.model.set('locality', null);
          this.model.trigger('change:locality', this.model);
          return val;
        },
      },
      '#document_locality': {
        observe: 'locality',
        selectOptions: {
          collection: function() {
            var country = Indigo.countries[this.country || this.model.get('country')];
            return country ? country.localities : [];
          },
          defaultOption: {label: "(none)", value: null},
        }
      },
      '#document_nature': 'nature',
      '#document_subtype': 'subtype',
      '#document_year': 'year',
      '#document_number': 'number',
      '#document_frbr_uri': 'frbr_uri',
      '#document_title': 'title',
      '#document_tags': {
        observe: 'tags',
        getVal: function($el, event, options) {
          return $el.val() || [];
        },
        update: function($el, val, model, options) {
          val = val || [];
          if (!$el.data('select2')) {
            $el.select2();
          }

          // update the valid choices to ensure those we want are there
          $el.select2({data: val});
          // add them
          $el.val(val).trigger('change');
        },
      },
      '#document_publication_date': {
        observe: 'publication_date',
        onSet: emptyIsNull,
      },
      '#document_publication_name': 'publication_name',
      '#document_publication_number': 'publication_number',
      '#document_commencement_date': {
        observe: 'commencement_date',
        onSet: emptyIsNull,
      },
      '#document_assent_date': {
        observe: 'assent_date',
        onSet: emptyIsNull,
      },
      '#document_expression_date': {
        observe: 'expression_date',
        onSet: emptyIsNull,
        selectOptions: {
          collection: 'this.expressionDates',
        }
      },
      '#document_language': 'language',
      '#document_draft': {
        observe: 'draft',
        onSet: bool,
      },
      '#document_stub': {
        observe: 'stub',
        onSet: bool,
      },
      '#document_updated_at': {
        observe: 'updated_at',
        onGet: function(value, options) {
          if (value) {
            value = moment(value).calendar();
            if (this.model.get('updated_by_user')) {
              value += ' by ' + this.model.get('updated_by_user').display_name;
            }
            return value;
          } else {
            return "";
          }
        }
      },
      '#document_created_at': {
        observe: 'created_at',
        onGet: function(value, options) {
          if (value) {
            value = moment(value).calendar();
            if (this.model.get('created_by_user')) {
              value += ' by ' + this.model.get('created_by_user').display_name;
            }
            return value;
          } else {
            return "";
          }
        }
      },
    },

    initialize: function() {
      // the choices in the expression_date dropdown
      this.expressionDates = new Backbone.Collection();

      this.dirty = false;
      this.model.on('change', this.setDirty, this);
      this.model.on('sync', this.setClean, this);
      this.model.expressionSet.on('change', this.setDirty, this);

      this.model.on('change:draft change:frbr_uri change:language change:expression_date sync', this.showPublishedUrl, this);
      this.model.on('change:repeal sync', this.showRepeal, this);

      // update the choices of expression dates when necessary
      this.model.on('change:publication_date', this.updateExpressionDates, this);
      this.model.expressionSet.amendments.on('change:date add remove reset', this.updateExpressionDates, this);

      this.calculateUri();
      this.updateExpressionDates();
      this.stickit();
    },

    updateExpressionDates: function() {
      var dates = this.model.expressionSet.allDates(),
          pubDate = this.model.expressionSet.initialPublicationDate();

      this.expressionDates.set(_.map(dates, function(date) {
        return {
          value: date,
          label: date + ' - ' + (date == pubDate ? 'initial publication' : 'amendment'),
        };
      }), {merge: false});
    },

    showAmendments: function(e) {
      e.preventDefault();
      $('.sidebar a[href="#amendments-tab"]').click();
    },

    calculateUri: function() {
      // rebuild the FRBR uri when one of its component sources changes
      var parts = [''];

      var country = this.model.get('country');
      if (this.model.get('locality')) {
        country += "-" + this.model.get('locality');
      }
      parts.push(country);
      parts.push(this.model.get('nature'));
      if (this.model.get('subtype')) {
        parts.push(this.model.get('subtype'));
      }
      parts.push(this.model.get('year'));
      parts.push(this.model.get('number'));

      // clean the parts
      parts = _.map(parts, function(p) { return p.replace(/[ \/]/g, ''); });

      this.model.set('frbr_uri', parts.join('/').toLowerCase());
    },

    showPublishedUrl: function() {
      var url = window.location.origin + "/api" +
        this.model.get('frbr_uri') + '/' + this.model.get('language');

      if (this.model.get('expression_date')) {
        url = url + '@' + this.model.get('expression_date');
      }

      this.$el.find('.published-url').toggle(!this.model.get('draft'));
      this.$el.find('#document_published_url').attr('href', url).text(url);
    },

    setDirty: function() {
      if (!this.dirty) {
        this.dirty = true;
        this.trigger('dirty');
      }
    },

    setClean: function() {
      if (this.dirty) {
        this.dirty = false;
        this.trigger('clean');
      }
    },

    save: function() {
      var self = this;
      // TODO: validation

      // don't do anything if it hasn't changed
      if (!this.dirty) {
        return $.Deferred().resolve();
      }

      // save modified documents using the expression set is sufficient to
      // ensure this document is saved too
      var dirty = this.model.expressionSet.filter(function(d) { return d.dirty; });

      // save the dirty ones and chain the deferreds into a single deferred
      return $.when.apply($, dirty.map(function(d) {
        return d.save();
      })).done(function() {
        self.setClean();
      });
    },
  });
})(window);
