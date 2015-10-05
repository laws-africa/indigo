(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.LibraryFilterView = Backbone.View.extend({
    el: '.workspace',
    template: '#filters-template',
    events: {
      'click .filter-tag': 'filterByTag',
      'change .filter-country': 'filterByCountry',
      'click .filter-locality': 'filterByLocality',
      'keyup .filter-search': 'filterBySearch',
      'change .filter-status': 'filterByStatus',
    },

    initialize: function() {
      var self = this;

      this.template = Handlebars.compile($(this.template).html());
      this.filtered = new Indigo.Library();
      this.filters = {
        search: null,
        country: null,
        locality: null,
        tags: [],
        status: 'all',
      };
      this.searchableFields = ['title', 'year', 'number', 'country', 'locality', 'subtype'];

      this.on('change', this.summarizeAndRender, this);

      this.model = new Indigo.Library();
      this.model.on('change reset', function() { this.trigger('change'); }, this);

      this.user = Indigo.userView.model;
      this.user.on('change:country_code sync', function() {
        var country = this.get('country_code');
        if (country) {
          country = country.toLowerCase();
          self.$el.find('.filter-country').val(country).change();
        }
      });
    },

    loadDocuments: function() {
      this.model.reset(Indigo.libraryPreload);
    },

    summarizeAndRender: function() {
      this.filterAndSummarize();
      this.render();
    },

    filterAndSummarize: function() {
      var filters = this.filters;
      var docs = this.model.models;

      this.summary = {};

      // ** country
      // count countries, sort alphabetically
      this.summary.countries = _.sortBy(
        _.map(
          _.countBy(docs, function(d) { return d.get('country'); }),
          function(count, code) {
            return {
              code: code,
              name: Indigo.countries[code],
              count: count,
              active: filters.country === code,
            };
          }
        ),
        function(info) { return info.name; });
      this.summary.show_countries = this.summary.countries.length > 1;
      // filter by country
      if (filters.country) {
        docs = _.filter(docs, function(doc) {
          return doc.get('country') == filters.country;
        });
      }

      // ** status
      // filter by status
      if (filters.status !== 'all') {
        docs = _.filter(docs, function(doc) {
          if (filters.status === "draft") {
            return doc.get('draft') === true;
          }
          else if (filters.status === "published"){
            return doc.get('draft') === false;
          }
        });
      }

      // ** locality
      // count localities, sort alphabetically
      this.summary.localities = _.sortBy(
        _.map(
          _.countBy(
            _.filter(docs, function(d) { return d.get('locality'); }),
                    function(d) { return d.get('locality'); }),
          function(count, code) {
            return {
              code: code,
              name: code || "(none)",
              count: count,
              active: filters.locality === code,
            };
          }
        ),
        function(info) { return info.code; });
      // filter by locality
      if (filters.locality) {
        docs = _.filter(docs, function(doc) {
          return doc.get('locality') == filters.locality;
        });
      }

      // ** tags
      // count tags, sort in descending order
      var tags = {};
      _.each(filters.tags, function(t) { tags[t] = 1; });

      this.summary.tags = _.sortBy(
        _.map(
          // count occurrences of each tag
          _.countBy(
            // build up a list of tags
            _.reduce(docs, function(list, d) { return list.concat(d.get('tags') || []); }, [])
          ),
          // turn counts into useful objects
          function(count, tag) {
            return {
              tag: tag,
              count: count,
              active: tags[tag],
            };
          }
        ),
        // sort most tagged to least
        function(info) { return -info.count; });
      // filter by tags
      if (filters.tags.length > 0) {
        docs = _.filter(docs, function(doc) {
          return _.all(filters.tags, function(tag) { return (doc.get('tags') || []).indexOf(tag) > -1; });
        });
      }

      // search
      if (filters.search) {
        var needle = filters.search.toLowerCase();
        var self = this;

        docs = _.filter(docs, function(doc) {
          return _.any(self.searchableFields, function(field) {
            var val = doc.get(field);
            return val && val.toLowerCase().indexOf(needle) > -1;
          });
        });
      }

      this.filtered.reset(docs);
    },

    filterByTag: function(e) {
      e.preventDefault();

      var $link = $(e.currentTarget);
      var tag = $link.data('tag');
      var ix = this.filters.tags.indexOf(tag);

      if (ix > -1) {
        $link.removeClass('label-info').addClass('label-default');
        this.filters.tags.splice(ix, 1);
      } else {
        $link.removeClass('label-default').addClass('label-info');
        this.filters.tags.push(tag);
      }

      this.trigger('change');
    },

    filterByCountry: function(e) {
      e.preventDefault();

      this.filters.country = $(e.currentTarget).val() || null;
      this.filters.locality = null;
      this.filters.tags = [];

      this.trigger('change');
    },

    filterByLocality: function(e) {
      e.preventDefault();

      this.filters.locality = $(e.currentTarget).data('locality') || null;
      this.filters.tags = [];

      this.trigger('change');
    },

    filterByStatus: function(e) {
      this.filters.status = $(e.currentTarget).val();
      this.trigger('change');
    },

    filterBySearch: function(e) {
      var needle = this.$el.find('.filter-search').val().trim();
      if (needle != this.filters.search) {
        this.filters.search = needle;
        this.trigger('change');
      }
    },

    render: function() {
      var filter_status = {};
      filter_status[this.filters.status] = 1;

      $('#filters').html(this.template({
        summary: this.summary,
        count: this.model.length,
        filters: this.filters,
        filter_status: filter_status,
      }));
    },
  });

  Indigo.LibraryView = Backbone.View.extend({
    el: '#library',
    template: '#search-results-template',
    events: {
      'click .document-list-table th': 'changeSort',
    },

    initialize: function() {
      this.template = Handlebars.compile($(this.template).html());

      this.sortField = 'updated_at';
      this.sortDesc = true;

      // the filter view does all the hard work of actually fetching and
      // filtering the documents
      this.filterView = new Indigo.LibraryFilterView();
      this.filterView.on('change', this.render, this);
      this.filterView.loadDocuments();
    },

    changeSort: function(e) {
      var field = $(e.target).data('sort');

      if (field == this.sortField) {
        // reverse
        this.sortDesc = !this.sortDesc;
      } else {
        this.sortField = field;
        this.sortDesc = false;
      }

      this.render();
    },

    render: function() {
      var docs = this.filterView.filtered;

      docs.comparator = this.sortField;
      docs.sort();

      docs = docs.toJSON();
      if (this.sortDesc) {
        docs.reverse();
      }

      this.$el.html(this.template({
        count: docs.length,
        documents: docs,
        sortField: this.sortField,
        sortDesc: this.sortDesc,
      }));

      this.$el.find('[title]').tooltip({
        container: 'body',
        placement: 'auto top'
      });

      this.$el.find('th[data-sort=' + this.sortField + ']').addClass(this.sortDesc ? 'sort-up' : 'sort-down');

      Indigo.relativeTimestamps();
    }
  });
})(window);
