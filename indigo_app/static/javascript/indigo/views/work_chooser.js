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
      'change .work-chooser-country': 'countryChanged',
      'change .work-chooser-locality': 'localityChanged',
      'click tr': 'itemClicked',
      'click .get-next-page': 'getNextPage',
      'hidden.bs.modal': 'dismiss',
      'shown.bs.modal': 'shown',
      'click .btn.choose-work': 'save',
    },

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());
      this.searchableFields = ['title', 'year', 'number'];

      this.chosen = null;
      this.filters = new Backbone.Model({
        country: options.country,
        locality: options.locality,
      });

      this.$el.on('keyup', '.work-chooser-search', _.debounce(_.bind(this.filterBySearch, this), 300));

      this.collection = new Indigo.WorksCollection();
      this.collection.params.page_size = 100;
      this.listenTo(this.collection, 'change reset add', this.render);
      this.listenTo(this.filters, 'change', this.refresh);

      this.$el.find('.modal-title').text(options.title);

      this.$el.find('.work-chooser-country').prop('disabled', options.disable_country);
      this.$el.find('.work-chooser-locality').prop('disabled', options.disable_locality);

      this.refresh();
      this.updateLocalities();
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

    itemClicked: function(e) {
      var id = $(e.target).closest('tr').data('id');
      this.choose(this.collection.get(id));
    },

    refresh: function() {
      var locality = this.filters.get('locality'),
          country = this.filters.get('country'),
          create_work_url = '/places/' + country;

      this.collection.country = country;
      this.collection.params.search = this.filters.get('search') || '';

      if (!locality) {
        delete this.collection.params.frbr_uri__starts_with;
      } else if (locality === "-") {
        this.collection.params.frbr_uri__startswith = '/akn/' + country + '/';
      } else {
        this.collection.params.frbr_uri__startswith = '/akn/' + country + '-' + locality + '/';
        create_work_url = create_work_url + '-' + locality;
      }

      this.collection.fetch({reset: true});

      this.$('.btn.create-work').attr('href', create_work_url + '/works/new/');
    },

    filterBySearch: function(e) {
      this.filters.set('search', $(e.target).val().trim());
    },

    countryChanged: function(e) {
      this.filters.set({
        country: e.target.selectedOptions[0].value,
        locality: null,
      });
      this.updateLocalities();
    },

    localityChanged: function(e) {
      this.filters.set('locality', e.target.selectedOptions[0].value);
    },

    updateLocalities: function() {
      var country = this.filters.get('country'),
          locality = this.filters.get('locality'),
          localities = _.clone(Indigo.countries[country].localities);
      var $select = this.$('select.work-chooser-locality')
        .empty()
        .toggle(!_.isEmpty(localities));

      localities.push({
        name: '(all localities)',
        code: '',
      });
      localities.push({
        name: '(none)',
        code: '-',
      });
      localities = _.sortBy(localities, function(x) { return x.name.toLocaleLowerCase(); });

      _.each(localities, function(loc) {
        var opt = document.createElement('option');
        opt.setAttribute('value', loc.code);
        opt.innerText = loc.name;
        opt.selected = loc.code === locality;
        $select.append(opt);
      });
    },

    getNextPage: function(e) {
      e.preventDefault();
      e.stopPropagation();
      this.collection.getNextPage();
    },

    render: function() {
      var works = this.collection,
          chosen = this.chosen;

      // ensure selections are up to date
      this.$('select.work-chooser-country option[value="' + this.filters.get('country') + '"]').attr('selected', true);

      // convert to json and add a chosen indicator
      works = works.map(function(d) {
        var json = d.toJSON();
        if (chosen && chosen === d) {
          json.chosen = true;
        }
        return json;
      });

      this.$el.find('.work-chooser-list').html(this.template({
        works: works,
        count: this.collection.length,
        pagination: {
          hasNextPage: this.collection.hasNextPage(),
        },
      }));
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

  // logic to hook up work chooser to buttons and inputs
  var summaryTemplate = $('#work-chooser-summary-template');
  if (summaryTemplate.length > 0) {
    summaryTemplate = Handlebars.compile(summaryTemplate.html());
    $('body').on('click', '.show-work-chooser', function(e) {
      var btn = e.target,
          country = btn.getAttribute('data-country'),
          input = document.querySelector(btn.getAttribute('data-input')),
          display = document.querySelector(btn.getAttribute('data-display')),
          chosen = input.value,
          chooser = new Indigo.WorkChooserView({country: country});

      chooser.showModal().done(function(chosen) {
        input.value = chosen.get('id');

        if (display) {
          display.innerHTML = summaryTemplate(chosen.toJSON());
        }
      });
    });
  }
})(window);
