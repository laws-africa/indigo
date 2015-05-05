(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.LibraryFilterView = Backbone.View.extend({
    el: '#filters',
    template: '#filters-template',

    initialize: function() {
      this.template = Handlebars.compile($(this.template).html());
      this.model.on('change, reset', this.summarizeAndRender, this);
    },

    summarizeAndRender: function() {
      this.summarize();
      this.render();
    },

    summarize: function() {
      var countries = {
        'za': 'South Africa',
        'zm': 'Zambia',
      };

      this.summary = {};

      // count countries, sort alphabetically
      this.summary.countries = _.sortBy(
        _.map(
          _.countBy(this.model.models, function(d) { return d.get('country'); }),
          function(count, code) { return {code: code, name: countries[code], count: count}; }
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

    render: function() {
      this.$el.html(this.template({summary: this.summary}));
    }
  });

  Indigo.LibraryView = Backbone.View.extend({
    el: '#library',
    template: '#search-results-template',

    initialize: function() {
      this.template = Handlebars.compile($(this.template).html());

      this.model = new Indigo.Library();
      this.model.on('change, reset', this.render, this);

      this.filterView = new Indigo.LibraryFilterView({model: this.model});

      // TODO: handle search
      this.listDocuments();
    },

    listDocuments: function() {
      var model = this.model;
      $.getJSON('/api/documents', function(docs) {
        model.reset(docs);
      });
    },

    render: function() {
      this.$el.html(this.template({
        count: this.model.length,
        documents: this.model.toJSON()
      }));
      formatTimestamps();
      this.$el.find('table').tablesorter({
        sortList: [[0, 0]],
        headers: {
          // sort timestamps as text, since they're iso8601
          4: {sorter: "text"},
        }
      });
    }
  });
})(window);
