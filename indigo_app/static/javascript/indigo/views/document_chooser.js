(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * A widget that lists documents and lets the user choose one.
   *
   * When the choice changes, a 'chosen' event is fired
   * on the view itself. The chosen document is in the
   * 'chosen' attribute.
   */
  Indigo.DocumentChooserView = Backbone.View.extend({
    template: '#document-chooser-template',
    events: {
      'keyup .document-chooser-search': 'filterBySearch',
      'click .document-chooser-search-clear': 'resetSearch',
      'click tr': 'itemClicked',
    },

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());
      this.searchableFields = ['title', 'year', 'number'];
      this.chosen = null;

      this.model = Indigo.library;
      this.listenTo(this.model, 'change reset', this.render);
      this.on('change:filter', this.render, this);

      this.setFilters({});
    },

    choose: function(item) {
      var document = this.model.get(item);
      this.chosen = document;
      this.render();
      this.trigger('chosen');
      // TODO: scroll into view if it's not visible
    },

    setFilters: function(filters) {
      this.filters = _.extend({
        search: null,
        country: null,
        tags: [],
        status: 'all',
      }, filters || {});

      this.trigger('change:filter');
    },

    itemClicked: function(e) {
      var ix = $(e.target).closest('tr').data('index');
      this.choose(this.filtered().at(ix));
    },

    filterBySearch: function(e) {
      var needle = $(e.target).val().trim();
      if (needle != this.filters.search) {
        this.filters.search = needle;
        this.trigger('change:filter');
      }
    },

    resetSearch: function(e) {
      this.$el.find('.document-chooser-search').val('').trigger('keyup');
    },

    render: function() {
      var docs = this.filtered();
      var chosen = this.chosen;

      // convert to json and add a chosen indicator
      docs = docs.map(function(d) {
        var json = d.toJSON();
        if (chosen && chosen == d) {
          json.chosen = true;
        }
        return json;
      });

      this.$el.find('.document-chooser-list').html(this.template({
        documents: docs,
        count: this.model.length,
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
})(window);
