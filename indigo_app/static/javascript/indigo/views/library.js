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
    el: '#library-view',
    template: '#filter-tags-template',
    events: {
      'click .filter-tag': 'filterByTag',
      'change .filter-country': 'changeCountry',
      'change .filter-locality': 'filterByLocality',
      'change .filter-subtype': 'filterBySubtype',
      'keyup .filter-search': 'filterBySearch',
      'change .filter-status': 'filterByStatus',
    },

    initialize: function() {
      var self = this;

      this.searchableFields = ['title', 'year', 'number', 'country', 'locality', 'subtype'];
      this.template = Handlebars.compile($(this.template).html());
      this.filtered = new Indigo.Library();
      this.filters = new Backbone.Model({
        country: Indigo.Preloads.country_code,
        locality: null,
        tags: [],
        status: 'all',
        search: null,
      });
      this.listenTo(this.filters, 'change', function() { this.trigger('change'); });
      this.listenTo(this.filters, 'change', this.saveState);
      this.loadState();

      this.listenTo(this, 'change', this.summarizeAndRender);

      this.works = Indigo.works;
      this.listenTo(this.works, 'change', function() { this.trigger('change'); });

      this.library = Indigo.library;
      this.listenTo(this.library, 'change reset', function() { this.trigger('change'); });
    },

    saveState: function() {
      // make the query string url
      var url = _.compact(_.map(this.filters.attributes, function(val, key) {
        if (key != 'search' && key != 'country' && !_.isNaN(val) && (_.isNumber(val) || !_.isEmpty(val))) return key + '=' + encodeURIComponent(val);
      })).join('&');

      history.replaceState({}, document.title, url ? ('?' + url) : "");
    },

    loadState: function() {
      var 
          tags = Indigo.queryParams.tags;
      if (tags) {
        tags = tags.split(',');
      }

      this.filters.set({
        country: this.filters.get('country'),
        locality: Indigo.queryParams.locality,
        status: Indigo.queryParams.status || 'all',
        subtype: Indigo.queryParams.subtype,
        tags: tags || [],
      });
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
     *  - subtype
     *  - status
     *  - tags
     *  - search
     */
    filterAndSummarize: function() {
      var filters = this.filters.attributes,
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
      var country = Indigo.countries[filters.country];

      // count localities, sort alphabetically
      this.summary.localities = _.sortBy(
        _.map(
          _.countBy(works, function(d) { return d.get('locality') || "-"; }),
          function(count, code) {
            var loc = country.localities[code];

            return {
              code: code,
              name: code == '-' ? '(none)' : (loc + ' · ' + code),
              count: count,
              active: filters.locality === code,
            };
          }
        ),
        function(info) { return info.code == '-' ? '' : info.name.toLocaleLowerCase(); });
      this.summary.localities.unshift({
        code: null,
        name: 'All localities',
        count: works.length,
        active: !!filters.locality,
      });

      // filter by locality
      if (filters.locality) {
        var loc = filters.locality == '-' ? null : filters.locality;
        works = _.filter(works, function(work) { return work.get('locality') == loc; });
      }

      // count subtype, sort alphabetically
      this.summary.subtypes = _.sortBy(
        _.map(
          _.countBy(works, function(d) { return d.get('subtype') || "-"; }),
          function(count, subtype) {
            return {
              subtype: subtype,
              name: subtype == '-' ? 'act' : subtype,
              count: count,
              active: filters.subtype === subtype,
            };
          }
        ),
        function(info) { return info.subtype; });
      this.summary.subtypes.unshift({
        subtype: null,
        name: 'All types',
        count: works.length,
        active: !!filters.subtype,
      });

      // filter by subtype
      if (filters.subtype) {
        var st = filters.subtype == '-' ? null : filters.subtype;
        works = _.filter(works, function(work) { return work.get('subtype') == st; });
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
      var ix = this.filters.get('tags').indexOf(tag);

      if (ix > -1) {
        $link.removeClass('label-info').addClass('label-default');
        this.filters.get('tags').splice(ix, 1);
        this.filters.trigger('change change:tags');
      } else {
        $link.removeClass('label-default').addClass('label-info');
        this.filters.get('tags').push(tag);
        this.filters.trigger('change change:tags');
      }
    },

    changeCountry: function(e) {
      e.preventDefault();
      var country = $(e.currentTarget).val();

      window.location = '/library/' + country + '/';
    },

    filterByLocality: function(e) {
      e.preventDefault();

      this.filters.set({
        locality: $(e.currentTarget).val(),
        subtype: null,
        tags: [],
      });
    },

    filterBySubtype: function(e) {
      e.preventDefault();

      this.filters.set({
        subtype: $(e.currentTarget).val(),
        tags: [],
      });
    },

    filterByStatus: function(e) {
      this.filters.set({
        status: $(e.currentTarget).val(),
        tags: [],
      });
    },

    filterBySearch: function(e) {
      var needle = this.$el.find('.filter-search').val().trim();
      if (needle != this.filters.get('search')) {
        this.filters.set('search', needle);
      }
    },

    render: function() {
      // localities
      var select = this.$('.filter-locality').empty();
      if (!this.summary.localities) {
        select.hide();
      } else {
        select.show();
        this.summary.localities.forEach(function(loc) {
          var option = document.createElement('option');
          option.value = loc.code || "";
          option.text = loc.name + " (" + loc.count + ")";
          option.selected = loc.active;
          select[0].add(option);
        });
      }

      // subtypes
      select = this.$('.filter-subtype').empty()[0];
      this.summary.subtypes.forEach(function(type) {
        var option = document.createElement('option');
        option.value = type.subtype || "";
        option.text = type.name + " (" + type.count + ")";
        option.selected = type.active;
        select.add(option);
      });

      // status
      var status = this.filters.get('status');
      this.$('.filter-status-all').toggleClass('active btn-primary', status == 'all');
      this.$('.filter-status-published').toggleClass('active btn-info', status == 'published');
      this.$('.filter-status-draft').toggleClass('active btn-warning', status == 'draft');

      $('#filter-tags').html(this.template({
        tags: this.summary.tags,
      }));
    },
  });

  Indigo.LibraryView = Backbone.View.extend({
    el: '#library',
    template: '#search-results-template',
    events: {
      'click .library-work-table th': 'changeSort',
      'click .toggle-docs': 'toggleDocuments',
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
    },

    changeSort: function(e) {
      var field = $(e.currentTarget).data('sort');

      if (field == this.sortField) {
        // reverse
        this.sortDesc = !this.sortDesc;
      } else {
        this.sortField = field;
        this.sortDesc = false;
      }

      this.render();
    },

    toggleDocuments: function(e) {
      e.preventDefault();
      var $link = $(e.currentTarget),
          work = $link.data('work'),
          $i = $link.find('i'),
          opened = $i.hasClass('fa-caret-down');

      $i
        .toggleClass('fa-caret-right', opened)
        .toggleClass('fa-caret-down', !opened);

      $('.library-work-table tr[data-work="' + work + '"]').toggleClass('d-none', opened);
    },

    render: function() {
      var works = this.filterView.filteredWorks,
          docs = this.filterView.filteredDocs,
          sortDesc = this.sortDesc;

      // tie works and docs together
      works = _.map(works, function(work) {
        var currentUserId = Indigo.user.get('id');

        work = work.toJSON();

        var work_docs = _.map(docs[work.id] || [], function(doc) {
          return doc.toJSON();
        });

        // distinct languages
        var languages = _.unique(_.map(work_docs, function(doc) {
          return doc.language;
        }));

        // alphabetise list of languages
        work.languages = languages.sort(function(a, b) {
          return a.localeCompare(b);
        });

        // number of distinct languages
        work.n_languages = work.languages.length;

        // count expression dates
        work.n_expressions = _.unique(_.map(work_docs, function(doc) {
          return doc.expression_date;
        })).length;

        // number of drafts
        work.drafts_v_published = _.countBy(work_docs, function(doc) {
          return doc.draft ? 'n_drafts': 'n_published';
        });

        if (work.drafts_v_published.n_drafts) {
          work.n_drafts = work.drafts_v_published.n_drafts;
        } else {
          work.n_drafts = 0;
        }

        // total number of docs
        work.n_docs = work_docs.length;

        // get a ratio of drafts vs total docs for sorting
        if (work.n_docs !== 0) {
          work.pub_ratio = 1 / (work.n_drafts / work.n_docs);
        } else {
          work.pub_ratio = 0;
        }

        // add work to list of docs and order by recency
        var work_and_docs = work_docs.concat([work]);

        var most_recently_updated = work_and_docs.sort(function(a, b) {
          return -a.updated_at.localeCompare(b.updated_at);
        })[0];

        work.updated_at = most_recently_updated.updated_at;

        // current user's name -> 'you'
        if (most_recently_updated.updated_by_user && most_recently_updated.updated_by_user.id == currentUserId) {
          most_recently_updated.updated_by_user.display_name = 'you';
        }

        work.most_recent_updated_by = most_recently_updated.updated_by_user;

        work_docs.forEach(function(work_doc) {
          if (work_doc.updated_by_user && work_doc.updated_by_user.id === currentUserId) {
            work_doc.updated_by_user.display_name = 'you';
          }
        });

        // docs for this work
        work.work_docs = _.sortBy(work_docs, 'expression_date');
        work.work_docs.reverse();

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
