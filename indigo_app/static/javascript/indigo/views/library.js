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
      'change .filter-subtype': 'filterBySubtype',
      'keyup .filter-search': 'filterBySearch',
      'change .filter-status': 'filterByStatus',
      'change .filter-stub': 'filterByStub',
      'change .sortby': 'changeSort',
    },

    initialize: function() {
      var self = this;

      this.searchableFields = ['title', 'year', 'number', 'subtype'];
      this.template = Handlebars.compile($(this.template).html());
      this.filtered = new Indigo.Library();
      this.filters = new Backbone.Model({
        country: Indigo.Preloads.country_code,
        tags: [],
        status: ['draft', 'published'],
        search: null,
        stub: 'excl',
      });
      this.sortField = 'updated_at';
      this.sortDesc = true;
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
      var tags = Indigo.queryParams.tags;
      if (tags) {
        tags = tags.split(',');
      }

      this.filters.set({
        country: this.filters.get('country'),
        status: (Indigo.queryParams.status || 'draft,published').split(','),
        subtype: Indigo.queryParams.subtype,
        tags: tags || [],
        stub: Indigo.queryParams.stub || 'excl',
      });

      this.$('.filter-stub').selectpicker('val', this.filters.get('stub'));
      this.$('.filter-status').selectpicker('val', this.filters.get('status'));
    },

    changeSort: function(e) {
      var field = e.target.value,
          desc = field[0] == '-';

      if (desc) field = field.substr(1);

      this.sortField = field;
      this.sortDesc = desc;

      this.trigger('change');
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
      var filterWorksByDocs = function(predicate, testWork, returnStubs) {
        return _.filter(works, function(work) {
          var id = work.get('id');
          var isStub = work.get('stub') || !docs[id] || docs[id].length === 0;

          if (testWork && predicate(work)) return true;

          if (returnStubs && isStub) return true;

          // test the documents
          docs[id] = _.filter(docs[id], predicate);
          return docs[id].length > 0;
        });
      };

      // filter by country -- works is scoped to country, so this should be all the works
      works = this.works.where({'country': filters.country});
      var country = Indigo.countries[filters.country];

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

      // filter by stub
      if (filters.stub) {
        var stub = {
          excl: false,
          only: true,
        }[filters.stub];
        if (stub !== undefined) works = _.filter(works, function(work) { return work.get('stub') == stub; });
      }

      // filter by subtype
      if (filters.subtype) {
        var st = filters.subtype == '-' ? null : filters.subtype;
        works = _.filter(works, function(work) { return work.get('subtype') == st; });
      }

      // setup our collection of documents for each work
      works.forEach(function(work) {
        docs[work.get('id')] = work.documents().models;
      });

      // stub works don't have any docs to filter on
      if (filters.status && filters.stub != 'only') {
        var draft = _.contains(filters.status, 'draft'),
            published = _.contains(filters.status, 'published');

        // filter documents by status
        works = filterWorksByDocs(function(doc) {
          return (draft && doc.get('draft') ||
                  published && !doc.get('draft'));
        }, false, true);
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
        }, false, false);
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
        }, true, false); // true to also test the work, not just its docs
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

    filterBySubtype: function(e) {
      e.preventDefault();

      this.filters.set({
        subtype: $(e.currentTarget).val(),
        tags: [],
      });
    },

    filterByStatus: function(e) {
      this.filters.set({
        status: $(e.target).val() || ['draft', 'published'],
        tags: [],
      });
    },

    filterByStub: function(e) {
      this.filters.set({
        stub: $(e.target).val(),
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
      // subtypes
      var select = this.$('.filter-subtype').empty()[0];
      this.summary.subtypes.forEach(function(type) {
        var option = document.createElement('option');
        option.value = type.subtype || "";
        option.text = type.name + " (" + type.count + ")";
        option.selected = type.active;
        select.add(option);
      });

      $('#filter-tags').html(this.template({
        tags: this.summary.tags,
      }));
    },
  });

  Indigo.LibraryView = Backbone.View.extend({
    el: '#library',
    template: '#search-results-template',
    events: {
      'click .toggle-docs': 'toggleDocuments',
      'click .list-group-item a': 'linkClicked',
      'shown.bs.collapse .work-extra-detail': 'workDetailToggled',
      'hidden.bs.collapse .work-extra-detail': 'workDetailToggled',
    },

    initialize: function() {
      this.template = Handlebars.compile($(this.template).html());

      // the filter view does all the hard work of actually fetching and
      // filtering the documents
      this.filterView = new Indigo.LibraryFilterView();
      this.filterView.on('change', this.render, this);
      this.filterView.trigger('change');
    },

    linkClicked: function(e) {
      // don't bubble to avoid collapsing the container unnecessarily
      e.stopPropagation();
    },

    workDetailToggled: function(e) {
      var row = e.target.parentNode,
          $icon = $(row).find('.collapse-indicator'),
          opened = $(e.target).hasClass('show');

      $icon.toggleClass('fa-caret-right', !opened)
           .toggleClass('fa-caret-down', opened);
    },

    render: function() {
      var works = this.filterView.filteredWorks,
          docs = this.filterView.filteredDocs;

      // tie works and docs together
      works = _.map(works, function(work) {
        var currentUserId = Indigo.user.get('id');

        work = work.toJSON();
        work.n_annotations = 0;

        var work_docs = _.map(docs[work.id] || [], function(doc) {
          return doc.toJSON();
        });

        // distinct languages
        work.n_languages = _.unique(_.map(work_docs, function(doc) {
          return doc.language;
        })).length;

        // count expression dates
        work.n_expressions = _.unique(_.map(work_docs, function(doc) {
          return doc.expression_date;
        })).length;

        // number of drafts
        work.drafts_v_published = _.countBy(work_docs, function(doc) {
          return doc.draft ? 'n_drafts': 'n_published';
        });

        // total number of docs
        work.n_docs = work_docs.length;
        work.n_docs_singular = work_docs.length == 1;

        work.n_published = work.drafts_v_published.n_published || 0;
        work.n_drafts = work.drafts_v_published.n_drafts || 0;
        work.n_docs_drafts_singular = work.n_drafts === 1;
        work.n_amendments = (Indigo.Preloads.work_n_amendments[work.id] || {}).n_amendments || 0;
        work.no_children = work.n_docs === 0 && work.n_amendments === 0;
        work.n_expected_docs = (1 + work.n_amendments) * (work.n_languages || 1);

        // get a ratio of drafts vs total docs for sorting
        if (work.n_docs !== 0) {
          work.drafts_ratio = 100 * (work.n_drafts / work.n_expected_docs);
          work.pub_ratio = 100 * (work.n_published / work.n_expected_docs);
        } else {
          work.drafts_ratio = 0;
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

          // number of annotations / comments on each doc and work
          work_doc.n_annotations = (Indigo.Preloads.document_annotations[work_doc.id] || {}).n_annotations || 0;
          work.n_annotations += work_doc.n_annotations;

          // task stats
          work_doc.task_stats = Indigo.Preloads.document_tasks[work_doc.id] || {};
          work_doc.task_stats.n_active_tasks = (work_doc.task_stats.n_open_tasks || 0) + (work_doc.task_stats.n_pending_review_tasks || 0);
          work_doc.task_stats.pending_task_ratio = 100 * ((work_doc.task_stats.n_pending_review_tasks || 0) / work_doc.task_stats.n_active_tasks) || 0;
          work_doc.task_stats.open_task_ratio = 100 * ((work_doc.task_stats.n_open_tasks || 0) / work_doc.task_stats.n_active_tasks) || 0;
        });

        work.task_stats = Indigo.Preloads.work_tasks[work.id] || {};
        work.task_stats.n_active_tasks = (work.task_stats.n_open_tasks || 0) + (work.task_stats.n_pending_review_tasks || 0);
        work.task_stats.pending_task_ratio = 100 * ((work.task_stats.n_pending_review_tasks || 0) / work.task_stats.n_active_tasks) || 0;
        work.task_stats.open_task_ratio = 100 * ((work.task_stats.n_open_tasks || 0) / work.task_stats.n_active_tasks) || 0;

        // docs for this work
        work.work_docs = _.sortBy(work_docs, 'expression_date');
        work.work_docs.reverse();

        return work;
      });

      works = _.sortBy(works, this.filterView.sortField);
      if (this.filterView.sortDesc) works.reverse();

      this.$el.html(this.template({
        count: works.length,
        works: works,
      }));

      this.$el.find('[title]').tooltip({
        container: 'body',
        placement: 'auto'
      });

      Indigo.relativeTimestamps();
    }
  });
})(window);
