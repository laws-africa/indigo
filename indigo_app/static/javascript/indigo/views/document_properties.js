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
          $el.select2({data: val, width: '100%'});
          // add them
          $el.val(val).trigger('change');
        },
      },
      '#document_expression_date': {
        observe: 'expression_date',
        onSet: emptyIsNull,
        selectOptions: {
          collection: 'this.expressionDates',
        }
      },
      '#document_language': 'language',
      '#document_stub': {
        observe: 'stub',
        onSet: bool,
      },
    },

    initialize: function() {
      // the choices in the expression_date dropdown
      this.expressionDates = new Backbone.Collection();
      this.amendments = new Indigo.WorkAmendmentCollection(Indigo.Preloads.amendments, {
        work: this.model,
      });

      this.dirty = false;
      this.listenTo(this.model, 'change', this.setDirty);
      this.listenTo(this.model, 'sync', this.setClean);
      this.listenTo(this.model, 'change:draft change:frbr_uri change:language change:expression_date sync', this.showPublishedUrl);

      // update the choices of expression dates when necessary
      this.listenTo(this.model, 'change:publication_date', this.matchPublicationExpressionDates);
      this.listenTo(this.model, 'change:publication_date', this.updateExpressionDates);
      this.listenTo(this.model, 'change:work', this.workChanged);
      this.listenTo(this.amendments, 'change add remove reset', this.updateExpressionDates);

      this.updateExpressionDates();
      this.stickit();

      this.render();
    },

    matchPublicationExpressionDates: function(model, new_value) {
      // if the publication date has changed and the expression date
      // matches the old publication date, change the expression date, too
      var old_pub_date = this.model.previous("publication_date");

      if (this.model.get("expression_date") == old_pub_date) {
        this.model.set("expression_date", new_value);
      }

      if (this.model.get("commencement_date") == old_pub_date) {
        this.model.set("commencement_date", new_value);
      }
    },

    updateExpressionDates: function() {
      var dates = _.unique(this.amendments.pluck('date')),
          pubDate = this.model.work.get('publication_date'),
          expDate = this.model.get('expression_date');

      if (pubDate && dates.indexOf(pubDate) == -1) dates.push(pubDate);
      dates.sort();

      if (dates.length > 0 && (!expDate || dates.indexOf(expDate) == -1)) {
        this.model.set('expression_date', dates[0]);
      }

      this.expressionDates.set(_.map(dates, function(date) {
        return {
          value: date,
          label: date + ' - ' + (date == pubDate ? 'initial publication' : 'amendment'),
        };
      }), {merge: false});
    },

    showAmendments: function(e) {
      e.preventDefault();
      $('.document-sidebar a[href="#amendments-tab"]').click();
    },

    showPublishedUrl: function() {
      var url = this.model.manifestationUrl();

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

      return this.model.save().done(function() {
        self.setClean();
      });
    },

    render: function() {
      var work = this.model.work;

      this.$('.document-work-title')
        .text(work.get('title'))
        .attr('href', '/works' + work.get('frbr_uri'));
    },

    workChanged: function() {
      this.amendments.work = this.model.work;
      this.amendments.fetch({reset: true});
      this.$('a.manage-amendments').attr('href', '/works' + this.model.work.get('frbr_uri') + '/amendments/');
      this.render();
    },
  });
})(window);
