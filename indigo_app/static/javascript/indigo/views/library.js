(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.LibraryFilterView = Backbone.View.extend({
    el: '#filters',
    template: '#filters-template',
    events: {
      'click .filter-tag': 'filterByTag',
      'click .filter-country': 'filterByCountry',
      'keyup .filter-search': 'filterBySearch',
      'click .filter-search-clear': 'resetSearch',
      'change .filter-status': 'filterByStatus',
    },

    initialize: function() {
      this.template = Handlebars.compile($(this.template).html());

      this.model = new Indigo.Library();
      this.model.on('change, reset', this.summarizeAndRender, this);

      this.filters = {
        search: null,
        country: null,
        tags: [],
        status: 'all',
      };

      this.searchableFields = ['title', 'year', 'number', 'country', 'locality', 'subtype'];

      this.loadDocuments();
    },

    loadDocuments: function() {
      var model = this.model;
      var self = this;

      $.getJSON('/api/documents', function(docs) {
        model.reset(docs);
        self.trigger('change');
      });
    },

    summarizeAndRender: function() {
      this.summarize();
      this.render();
    },

    summarize: function() {
      this.summary = {};

      // count countries, sort alphabetically
      this.summary.countries = _.sortBy(
        _.map(
          _.countBy(this.model.models, function(d) { return d.get('country'); }),
          function(count, code) { return {code: code, name: Indigo.countries[code], count: count}; }
        ),
        function(info) { return info.name; });

      // count tags, sort in descending order
      this.summary.tags = _.sortBy(
        _.map(
          // count occurrences of each tag
          _.countBy(
            // build up a list of tags
            _.reduce(this.model.models, function(list, d) { return list.concat(d.get('tags') || []); }, [])
          ),
          // turn counts into useful objects
          function(count, tag) { return {tag: tag, count: count}; }
        ),
        // sort most tagged to least
        function(info) { return -info.count; });
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

      var $link = $(e.currentTarget);
      var country = $link.data('country') || null;

      $link.parent().children('.active').removeClass('active');
      $link.addClass('active');
      this.filters.country = country;

      this.trigger('change');
    },

    filterByStatus: function(e) {
      var $input = $(e.currentTarget);
      var status = $input.val();

      this.filters.status = status;

      // Change buttons to correct colour.
      var parent = $input.parent();
      parent.siblings().removeClass().addClass('btn btn-sm btn-default');

      if (status=='draft') {
        parent.removeClass().addClass('btn btn-sm btn-warning');
      }
      else if (status=='published') {
        parent.removeClass().addClass('btn btn-sm btn-info');
      }
      else {
        parent.removeClass().addClass('btn btn-sm btn-default');
      }

      this.trigger('change');
    },

    filterBySearch: function(e) {
      var needle = this.$el.find('.filter-search').val().trim();
      if (needle != this.filters.search) {
        this.filters.search = needle;
        this.trigger('change');
      }
    },

    resetSearch: function(e) {
      this.$el.find('.filter-search').val('').trigger('keyup');
    },

    render: function() {
      this.$el.html(this.template({
        summary: this.summary,
        count: this.model.length
      }));
    },

    // filter the documents according to our filters
    filtered: function() {
      var filters = this.filters;
      var collection = new Indigo.Library();
      var docs = this.model.models;

      // country
      if (filters.country) {
        docs = _.filter(docs, function(doc) {
          return doc.get('country') == filters.country;
        });
      }

      // tags
      if (filters.tags.length > 0) {
        docs = _.filter(docs, function(doc) {
          return _.all(filters.tags, function(tag) { return (doc.get('tags') || []).indexOf(tag) > -1; });
        });
      }

      // status
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

      collection.reset(docs);
      return collection;
    },
  });

  Indigo.LibraryView = Backbone.View.extend({
    el: '#library',
    template: '#search-results-template',

    initialize: function() {
      this.template = Handlebars.compile($(this.template).html());

      // the filter view does all the hard work of actually fetching and
      // filtering the documents
      this.filterView = new Indigo.LibraryFilterView();
      this.filterView.on('change', this.render, this);
    },

    render: function() {
      var docs = this.filterView.filtered();

      this.$el.html(this.template({
        count: docs.length,
        documents: docs.toJSON()
      }));


      this.$el.find('[title]').tooltip({
        container: 'body',
        placement: 'auto top'
      });

      formatTimestamps();

      this.$el.find('table').tablesorter({
        sortList: [[2, 0], [3, 0]],
        headers: {
          // sort timestamps as text, since they're iso8601
          3: {sorter: "text"},
        }
      });
    }
  });
})(window);
