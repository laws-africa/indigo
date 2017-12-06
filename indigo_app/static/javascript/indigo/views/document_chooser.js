(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * A widget that lists documents and lets the user choose one, or lets them build
   * up an FRBR uri for one.
   */
  Indigo.DocumentChooserView = Backbone.View.extend({
    el: '#document-chooser-box',
    template: '#document-chooser-template',
    events: {
      'keyup .document-chooser-search': 'filterBySearch',
      'click .document-chooser-search-clear': 'resetSearch',
      'click tr': 'itemClicked',
      'hidden.bs.modal': 'dismiss',
      'click .btn.save': 'save',
    },
    bindings: {
      '#chooser_doc_title': 'title',
      '#chooser_doc_date': 'expression_date',
      '#chooser_doc_number': 'number',
      '#chooser_doc_country': {
        observe: 'country',
        onSet: function(val) {
          // trigger a redraw of the localities, using this country
          this.country = val;
          this.model.set('locality', null);
          this.model.trigger('change:locality', this.model);
          return val;
        },
      },
      '#chooser_doc_subtype': 'subtype',
      '#chooser_doc_frbr_uri': 'frbr_uri',
      '#chooser_doc_locality': {
        observe: 'locality',
        selectOptions: {
          collection: function() {
            var country = Indigo.countries[this.country || this.model.get('country')];
            return country ? country.localities : [];
          },
          defaultOption: {label: "(none)", value: null},
        }
      },
    },

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());
      this.model = options.model ? options.model : new Indigo.Document();
      this.searchableFields = ['title', 'year', 'number'];
      this.chosen = null;

      this.collection = Indigo.library;
      this.listenTo(this.collection, 'change reset', this.render);
      this.on('change:filter', this.render, this);

      this.listenTo(this.model, 'change:expression_date', this.updateYear);
      this.stickit();

      this.$el.find('.modal-title').text(options.title);
      this.$el.find('.noun').text(options.noun);
      this.$el.find('.verb').text(options.verb);

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

    updateYear: function() {
      this.model.set('year', (this.model.get('expression_date') || "").split('-')[0]);
    },

    choose: function(item) {
      if (item) this.model.set(item.attributes);
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
        count: this.collection.length,
      }));

      // TODO: scroll active item into view
    },

    // filter the documents according to our filters
    filtered: function() {
      var filters = this.filters;
      var collection = new Indigo.Library();
      var docs = this.collection.models;

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

    dismiss: function() {
      this.close();
      this.deferred.reject();
    },

    save: function() {
      var item;

      this.close();

      // use the manual model, or the picked one?
      if (this.$el.find('#tab-document-list').hasClass('active')) {
        item = this.chosen;
      } else {
        item = this.model;
      }

      this.deferred.resolve(item);
    },

    close: function() {
      this.unstickit();
      this.stopListening();
      this.$el.modal('hide');
    },
  });
})(window);
