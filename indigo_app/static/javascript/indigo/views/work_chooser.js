(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * A widget that lists works and lets the user choose one, or lets them build
   * up an FRBR uri for one.
   */
  Indigo.WorkChooserView = Backbone.View.extend({
    el: '#work-chooser-box',
    template: '#work-chooser-table-template',
    events: {
      'keyup .work-chooser-search': 'filterBySearch',
      'click .work-chooser-search-clear': 'resetSearch',
      'change .work-chooser-country': 'countryChanged',
      'click tr': 'itemClicked',
      'hidden.bs.modal': 'dismiss',
      'shown.bs.modal': 'shown',
      'click .btn.choose-work': 'save',
    },

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());
      this.searchableFields = ['title', 'year', 'number'];
      this.chosen = null;

      this.collection = Indigo.works;
      this.listenTo(this.collection, 'change reset', this.render);
      this.on('change:filter', this.render, this);

      this.$el.find('.modal-title').text(options.title);

      this.setFilters({});
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

    choose: function(item) {
      this.chosen = this.collection.get(item);
      if (!this.chosen && item) {
        this.$el.find('.nav li:eq(1) a').click();
      } else {
        this.$el.find('.nav li:eq(0) a').click();
      }

      this.render();
    },

    setFilters: function(filters) {
      this.filters = _.extend({
        search: null,
        country: Indigo.works.country,
        tags: [],
        status: 'all',
      }, filters || {});

      this.trigger('change:filter');
    },

    itemClicked: function(e) {
      var id = $(e.target).closest('tr').data('id');
      this.choose(this.collection.get(id));
    },

    filterBySearch: function(e) {
      var needle = $(e.target).val().trim();
      if (needle != this.filters.search) {
        this.filters.search = needle;
        this.trigger('change:filter');
      }
    },

    resetSearch: function(e) {
      this.$el.find('.work-chooser-search').val('').trigger('keyup');
    },

    countryChanged: function(e) {
      this.filters.country = e.target.selectedOptions[0].value;
      Indigo.works.setCountry(this.filters.country);
    },

    render: function() {
      var works = this.filtered();
      var chosen = this.chosen;

      // ensure selections are up to date
      if (this.filters.country) {
        this.$('select.work-chooser-country option[value="' + this.filters.country + '"]').attr('selected', true);
      }

      // convert to json and add a chosen indicator
      works = works.map(function(d) {
        var json = d.toJSON();
        if (chosen && chosen == d) {
          json.chosen = true;
        }
        return json;
      });

      this.$el.find('.work-chooser-list').html(this.template({
        works: works,
        count: this.collection.length,
      }));
    },

    // filter the works according to our filters
    filtered: function() {
      var filters = this.filters;
      var collection = new Indigo.Library();
      var works = this.collection.models;

      // country
      if (filters.country) {
        works = _.filter(works, function(doc) {
          return doc.get('country') == filters.country;
        });
      }

      // tags
      if (filters.tags.length > 0) {
        works = _.filter(works, function(doc) {
          return _.all(filters.tags, function(tag) { return (doc.get('tags') || []).indexOf(tag) > -1; });
        });
      }

      // search
      if (filters.search) {
        var needle = filters.search.toLowerCase();
        var self = this;

        works = _.filter(works, function(doc) {
          return _.any(self.searchableFields, function(field) {
            var val = doc.get(field);
            return val && val.toLowerCase().indexOf(needle) > -1;
          });
        });
      }

      // sort by year (desc) then title (asc)
      collection.comparator = function(a, b) {
        if (a.get('year') == b.get('year')) {
          return a.get('title').localeCompare(b.get('title'));
        }

        return (b.get('year') - a.get('year'));
      };

      collection.reset(works);
      return collection;
    },

    dismiss: function() {
      this.close();
      this.deferred.reject();
    },

    shown: function() {
      // scroll selected item into view
      var item = this.$('.work-chooser-list tr.chosen')[0];
      if (item) item.scrollIntoView();
    },

    save: function() {
      this.close();
      this.deferred.resolve(this.chosen);
    },

    close: function() {
      this.stopListening();
      this.$el.modal('hide');
    },
  });
})(window);
