(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // Handle the document properties form, and saving them back to the server.
  Indigo.DocumentPropertiesView = Backbone.View.extend({
    el: '#props-tab article',
    bindings: {
      '#document_title': 'title',
      '#document_country': 'country',
      '#document_frbr_uri': 'frbr_uri',
      '#document_publication_date': 'publication_date',
      '#document_publication_name': 'publication_name',
      '#document_publication_number': 'publication_number',
      '#document_number': 'number',
      '#document_nature': 'nature',
      '#document_language': 'language',
      '#document_draft': {
        observe: 'draft',
        // API requires this value to be true or false
        onSet: function(val) { return val == "1"; }
      },
      '#document_updated_at': {
        observe: 'updated_at',
        onGet: function(value, options) {
          return value ? moment(value).calendar() : "";
        }
      },
      '#document_created_at': {
        observe: 'created_at',
        onGet: function(value, options) {
          return moment(value).calendar();
        }
      },
    },

    initialize: function() {
      this.stickit();

      this.dirty = false;
      this.model.on('change', this.setDirty, this);
      this.model.on('sync', this.setClean, this);

      // only attach URI building handlers after the first sync
      this.listenToOnce(this.model, 'sync', function() {
        this.model.on('change:number change:nature change:country change:publication_date', _.bind(this.calculateUri, this));
      });

      this.model.on('change:draft change:frbr_uri change:language', this.showPublishedUrl, this);
    },

    calculateUri: function() {
      // rebuild the FRBR uri when one of its component sources changes
      var parts = [
        '',
        this.model.get('country'),
        this.model.get('nature'),
        this.model.get('publication_date').split('-')[0],
        this.model.get('number')];
      this.model.set('frbr_uri', parts.join('/'));
    },

    showPublishedUrl: function() {
      var url = window.location.origin + "/api" +
        this.model.get('frbr_uri') + '/' + this.model.get('language');

      this.$el.find('.published-url').toggle(!this.model.get('draft'));
      this.$el.find('#document_published_url').attr('href', url).text(url);
    },

    setDirty: function() {
      if (!this.dirty) {
        this.dirty = true;
        this.trigger('dirty');
      }
    },

    setClean: function() {
      if (this.dirty) {
        this.dirty = false;
        this.trigger('clean');
      }
    },

    save: function() {
      // TODO: validation
      var self = this;

      // don't do anything if it hasn't changed
      if (!this.dirty) {
        return $.Deferred().resolve();
      }

      return this.model
        .save()
        .done(function() {
          self.model.attributes.updated_at = moment().format();
        });
    },
  });
})(window);
