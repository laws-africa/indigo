(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * The filter view takes various filter settings from the user
   * and determines which works and documents to show.
   *
   * Each time a filter is changed, this view's 'change' event is fired
   * and: 
   *   - filteredWorks is a collection of the works to show
   *   - filteredDocs is a map from work id to a collection of docs to show for each work
   *
   * Most filtering is done on the works, but some fields (such as title) are search for
   * both on a work and its documents, because a document can have a different title to a
   * work.
   */
  Indigo.LibraryFilterView = Backbone.View.extend({
    el: '.workspace',
    template: '#filters-template',
    events: {
      'click .filter-tag': 'filterByTag',
      'change .filter-country': 'changeCountry',
      'change .filter-locality': 'filterByLocality',
      'keyup .filter-search': 'filterBySearch',
      'change .filter-status': 'filterByStatus',
    },

    initialize: function() {
      var self = this;

      this.template = Handlebars.compile($(this.template).html());
      this.filtered = new Indigo.Library();
      this.filters = {
        search: null,
        country: Indigo.Preloads.country_code,
        locality: null,
        tags: [],
        status: 'all',
      };
      this.searchableFields = ['title', 'year', 'number', 'country', 'locality', 'subtype'];

      this.listenTo(this, 'change', this.summarizeAndRender);

      this.works = Indigo.works;
      this.listenTo(this.works, 'change', function() { this.trigger('change'); });

      this.library = Indigo.library;
      this.listenTo(this.library, 'change reset', function() { this.trigger('change'); });
    },

    summarizeAndRender: function() {
      this.filterAndSummarize();
      this.render();
    },

    /**
     * Filter the works/docs and calculate summary counts.
     *
     * These are intertwined because we generally need to summarise a field
     * just before we filter by it (eg. tags), but after preceding filters have
     * been applied. The order is:
     *
     *  - country
     *  - locality
     *  - status
     *  - tags
     *  - search
     */
    filterAndSummarize: function() {
      var filters = this.filters,
          works,
          docs = {};

      this.summary = {};

      // Helper to choose works by applying a predicate to each work's documents.
      var filterWorksByDocs = function(predicate, testWork) {
        return _.filter(works, function(work) {
          if (testWork && predicate(work)) return true;

          // test the documents
          var id = work.get('id');
          docs[id] = _.filter(docs[id], predicate);
          return docs[id].length > 0;
        });
      };

      // filter by country -- works is scoped to country, so this should be all the works
      works = this.works.where({'country': filters.country});

      // count localities, sort alphabetically
      this.summary.localities = _.sortBy(
        _.map(
          _.countBy(
            _.filter(works, function(d) { return d.get('locality'); }),
                    function(d) { return d.get('country') + '/' + d.get('locality'); }),
          function(count, code) {
            var parts = code.split('/'),
                country = Indigo.countries[parts[0]],
                loc_code = parts[1],
                loc = country ? country.localities[loc_code] : null;

            return {
              code: code,
              name: loc || loc_code,
              count: count,
              active: filters.locality === code,
            };
          }
        ),
        function(info) { return info.code; });

      // filter by locality
      if (filters.locality) {
        var parts = filters.locality.split('/'),
            country = parts[0],
            loc = parts[1];

        works = _.filter(works, function(work) {
          return work.get('country') == country && work.get('locality') == loc;
        });
      }

      // setup our collection of documents for each work
      works.forEach(function(work) {
        docs[work.get('id')] = work.documents().models;
      });

      if (filters.status !== 'all') {
        // filter documents by status
        works = filterWorksByDocs(function(doc) {
          return (filters.status === "draft" && doc.get('draft') ||
                  filters.status === "published" && !doc.get('draft'));
        });
      }

      // count tags, sort in descending order
      var tags = {};
      _.each(filters.tags, function(t) { tags[t] = 1; });

      // pull all the docs together
      var allDocs = _.reduce(works, function(list, w) { return list.concat(docs[w.get('id')] || []); }, []);
      this.summary.tags = _.sortBy(
        _.map(
          // count occurrences of each tag
          _.countBy(
            // build up a list of tags
            _.reduce(allDocs, function(list, d) { return list.concat(d.get('tags') || []); }, [])
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

      if (filters.tags.length > 0) {
        // filter documents by tags
        works = filterWorksByDocs(function(doc) {
          return _.all(filters.tags, function(tag) { return (doc.get('tags') || []).indexOf(tag) > -1; });
        });
      }

      // do search on both works and docs
      if (filters.search) {
        var needle = filters.search.toLowerCase();
        var fields = this.searchableFields;

        works = filterWorksByDocs(function(x) {
          return _.any(fields, function(field) {
            var val = x.get(field);
            return val && val.toLowerCase().indexOf(needle) > -1;
          });
        }, true); // true to also test the work, not just its docs
      }

      this.filteredWorks = works;
      this.filteredDocs = docs;
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

    changeCountry: function(e) {
      var self = this,
          country = $(e.currentTarget).val();

      e.preventDefault();

      Indigo.works.setCountry(country).done(function() {
        self.filters.country = country;
        self.filters.locality = null;
        self.filters.tags = [];

        // this will eventually trigger a change event on us
        Indigo.library.setCountry(self.filters.country);
      });
    },

    filterByLocality: function(e) {
      e.preventDefault();

      this.filters.locality = $(e.currentTarget).val() || null;
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
        count: this.works.length,
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
      this.filterView.trigger('change');
      Indigo.userView.model.on('change', this.render, this);
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
      var works = this.filterView.filteredWorks,
          docs = this.filterView.filteredDocs,
          sortDesc = this.sortDesc;

      // tie works and docs together
      works = _.map(works, function(work) {
        var currentUserId = Indigo.userView.model.get('id');

        work = work.toJSON();

        work.docs = _.map(docs[work.id] || [], function(d) { return d.toJSON(); });
        // latest expression first
        work.docs = _.sortBy(work.docs, 'expression_date');
        work.docs.reverse();

        // current user's name -> you
        work.docs.forEach(function(d, i) {
          if (d.updated_by_user && d.updated_by_user.id == currentUserId) d.updated_by_user.display_name = 'you';

          // only show doc titles that are different to the work
          if (i > 0 && d.title == work.title) d.title = '';
        });

        if (work.docs.length > 0) {
          var dates = _.compact(_.pluck(work.docs, 'updated_at'));
          dates.sort();

          // if we're sorting works by date later on, sort using the youngest/oldest, as appropriate
          work.updated_at = sortDesc ? dates.slice(-1) : dates[0];
        }

        return work;
      });

      works = _.sortBy(works, this.sortField);
      if (sortDesc) works.reverse();

      this.$el.html(this.template({
        count: works.length,
        works: works,
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
