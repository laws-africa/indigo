(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // django doesn't link blank date fields, send null instead
  function emptyIsNull(val) {
    return (!val || val.trim() === "") ? null : val;
  }

  function idOrNull(val) {
    return val ? val.get('id') : null;
  }

  /**
   * A view that lets a user create or edit a Work.
   *
   * This view supplements the actual HTML form on the work page
   * by filling in some fields (such as the frbr_uri) based on other
   * form widgets. It keeps the Backbone model up-to-date with the form
   * to help us make use of updated form elements elsewhere on the page.
   */
  Indigo.WorkDetailView = Backbone.View.extend({
    el: '#edit-work-view',
    events: {
      'change #edit-work-form': 'setDirty',
      'submit #edit-work-form': 'onSubmit',
      'click .delete-publication-document': 'deletePublicationDocument',
      'change #id_work-publication_document_file': 'publicationDocumentFileChanged',
      'click .attach-publication-url': 'attachPublicationUrl',
    },
    publicationDocumentTemplate: '#publication-document-template',
    publicationUrlTemplate: '#publication-document-url-template',
    bindings: {
      '#id_work-publication_date': {
        observe: 'publication_date',
        onSet: emptyIsNull,
      },
      '#id_work-publication_name': 'publication_name',
      '#id_work-publication_number': 'publication_number',

      '#id_work-country': {
        observe: 'country',
        onSet: function(val) {
          // map from numeric to text code
          var country = _.findWhere(_.values(Indigo.countries), {id: parseInt(val)});
          this.country = country ? country.code : null;

          // trigger a redraw of the localities, using this country
          this.model.set('locality', null);
          this.model.trigger('change:locality', this.model);

          return this.country;
        },
        onGet: function(code) {
          // map from text code to numeric
          var country = Indigo.countries[code];
          return country ? String(country.id) : null;
        }
      },
      '#id_work-locality': {
        observe: 'locality',
        onSet: function(id) {
          // map from numeric code to text code
          id = parseInt(id);
          var country = Indigo.countries[this.model.get('country')];
          var locality = country ? country.localities.find((loc) => loc.id === id) : null;
          return locality ? locality.code : null;
        },
        onGet: function(code) {
          // map from text code to numeric code
          var country = Indigo.countries[this.model.get('country')];
          var locality = country ? country.localities.find((loc) => loc.code === code) : null;
          return locality ? String(locality.id) : null;
        },
        selectOptions: {
          collection: function() {
            const country = Indigo.countries[this.country || this.model.get('country')];
            const localities = {};
            for (const loc of (country ? country.localities : [])) {
              localities[loc.id] = loc.name;
            }
            return localities;
          },
          defaultOption: {label: "(none)", value: null},
        }
      },
    },

    initialize: function(options) {
      this.dirty = false;
      this.saving = false;

      this.publicationDocumentTemplate = Handlebars.compile($(this.publicationDocumentTemplate).html());
      this.publicationUrlTemplate = Handlebars.compile($(this.publicationUrlTemplate).html());

      this.model = new Indigo.Work(Indigo.Preloads.work, {parse: true});
      this.listenTo(this.model, 'change', this.setDirty);
      this.listenTo(this.model, 'change:publication_document', this.publicationDocumentChanged);
      this.listenTo(this.model, 'change:publication_date change:publication_name change:publication_number',
                    _.debounce(this.publicationChanged, 1000));

      this.model.updateFrbrUri();
      this.stickit();
      this.publicationChanged();
      this.publicationDocumentChanged();
    },

    setDirty: function() {
      this.dirty = true;
    },

    setClean: function() {
      this.dirty = false;
    },

    onSubmit: function() {
      this.saving = true;
    },

    publicationChanged: function() {
      var date = this.model.get('publication_date'),
          number = this.model.get('publication_number'),
          publication = this.model.get('publication_name'),
          country = this.model.get('country'),
          $container = this.$('.work-publication-links'),
          template = this.publicationUrlTemplate;

      if (date && number) {
        var url = '/api/publications/' + country + '/find' + 
                  '?date=' + encodeURIComponent(date) + 
                  '&publication=' + encodeURIComponent(publication) +
                  '&number=' + encodeURIComponent(number);

        $.getJSON(url)
          .done(function(response) {
            $container.find('.publication-url, .h6').remove();
            $container.prepend(template(response));
          });
      }
    },

    publicationDocumentFileChanged: function(e) {
      var files = e.originalEvent.target.files,
          file = files.length > 0 ? files[0] : null;

      if (file) {
        this.model.set('publication_document', {
          size: file.size,
          mime_type: file.type,
          filename: file.name,
        });
      }
    },

    attachPublicationUrl: function(e) {
      var elem = e.currentTarget.parentElement;

      this.model.set('publication_document', {
        size: parseInt(elem.getAttribute('data-size')) || null,
        mime_type: elem.getAttribute('data-mime-type'),
        trusted_url: elem.getAttribute('data-url'),
        filename: elem.getAttribute('data-url'),
        url: elem.getAttribute('data-url'),
      });
    },

    publicationDocumentChanged: function() {
      var pub_doc = this.model.get('publication_document'),
          wrapper = this.$('.publication-document-wrapper').empty();

      if (pub_doc) {
        pub_doc.prettySize = Indigo.formatting.prettyFileSize(pub_doc.size);
        wrapper.append(this.publicationDocumentTemplate(pub_doc));
        this.$('.publication-document-file').hide();
        this.$('#id_work-delete_publication_document').val('');

        // from the trusted url, will be ignored if we've attached a file
        this.$('#id_work-publication_document_trusted_url').val(pub_doc.trusted_url);
        this.$('#id_work-publication_document_mime_type').val(pub_doc.mime_type);
        this.$('#id_work-publication_document_size').val(pub_doc.size);
      } else {
        this.$('#id_work-delete_publication_document').val('on');
        this.$('.publication-document-file').show();
      }
    },

    deletePublicationDocument: function(e) {
      e.preventDefault();

      this.$('#id_work-publication_document_file')[0].value = '';
      this.model.set('publication_document', null);
    },

    isDirty: function() {
      return !this.saving && this.dirty;
    },
  });

  Indigo.BatchAddWorkView = Backbone.View.extend({
    el: '#bulk-import-works-view',

    events: {
      'click .btn.show-progress': 'showProgress',
    },

    showProgress: function(e) {
      document.getElementById('import-progress').classList.remove('d-none');
    },
  });
})(window);
