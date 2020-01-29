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
      'click .change-repeal': 'changeRepeal',
      'click .delete-repeal': 'deleteRepeal',
      'click .choose-parent': 'changeParent',
      'click .delete-parent': 'deleteParent',
      'click .change-commencing-work': 'changeCommencingWork',
      'click .delete-commencing-work': 'deleteCommencingWork',
      'click .delete-publication-document': 'deletePublicationDocument',
      'change #id_work-publication_document_file': 'publicationDocumentFileChanged',
      'click .attach-publication-url': 'attachPublicationUrl',
      'change #commencement_date_unknown': 'commencementDateUnknownChanged',
    },
    workRepealTemplate: '#work-repeal-template',
    commencingWorkTemplate: '#commencing-work-template',
    publicationDocumentTemplate: '#publication-document-template',
    publicationUrlTemplate: '#publication-document-url-template',
    bindings: {
      // these are handled directly by the HTML form, but we need the values
      // to by synchronised on the model so that we can use them elsewhere on the page
      '#id_work-title': 'title',
      '#id_work-publication_date': {
        observe: 'publication_date',
        onSet: emptyIsNull,
      },
      '#id_work-publication_name': 'publication_name',
      '#id_work-publication_number': 'publication_number',
      '#id_work-commenced': 'commenced',
      '#id_work-commencement_date': {
        observe: 'commencement_date',
        onSet: emptyIsNull,
      },
      '#id_work-repealed_date': {
        observe: 'repealed_date',
        onSet: emptyIsNull,
      },
      '#id_work-parent_work': {
        observe: 'parent_work',
        onGet: idOrNull,
      },
      '#id_work-commencing_work': {
        observe: 'commencing_work',
        onGet: idOrNull,
      },
      '#id_work-repealed_by': {
        observe: 'repealed_by',
        onGet: idOrNull,
      },

      // actual frbr_uri
      '#id_work-frbr_uri': 'frbr_uri',
      // shows the FRBR uri as text
      '#work_frbr_uri': 'frbr_uri',

      // These are special and help backbone build up the frbr_uri
      '#work_country': {
        observe: 'country',
        onSet: function(val) {
          // trigger a redraw of the localities, using this country
          this.country = val;
          this.model.set('locality', null);
          this.model.trigger('change:locality', this.model);
          return val;
        },
      },
      '#work_locality': {
        observe: 'locality',
        selectOptions: {
          collection: function() {
            var country = Indigo.countries[this.country || this.model.get('country')];
            return country ? country.localities : [];
          },
          defaultOption: {label: "(none)", value: null},
        }
      },
      '#work_subtype': 'subtype',
      '#work_year': 'year',
      '#work_number': 'number',
    },

    initialize: function(options) {
      this.dirty = false;
      this.saving = false;

      this.workRepealTemplate = Handlebars.compile($(this.workRepealTemplate).html());
      this.commencingWorkTemplate = Handlebars.compile($(this.commencingWorkTemplate).html());
      this.publicationDocumentTemplate = Handlebars.compile($(this.publicationDocumentTemplate).html());
      this.publicationUrlTemplate = Handlebars.compile($(this.publicationUrlTemplate).html());
      this.commencementDateUnknown = document.getElementById('commencement_date_unknown');

      this.model = new Indigo.Work(Indigo.Preloads.work, {parse: true});
      this.listenTo(this.model, 'change:title change:frbr_uri', this.updatePageTitle);
      this.listenTo(this.model, 'change', this.setDirty);
      this.listenTo(this.model, 'change:repealed_by', this.repealChanged);
      this.listenTo(this.model, 'change:commenced', this.commencedChanged);
      this.listenTo(this.model, 'change:commencing_work', this.commencingWorkChanged);
      this.listenTo(this.model, 'change:parent_work', this.parentChanged);
      this.listenTo(this.model, 'change:number', this.numberChanged);
      this.listenTo(this.model, 'change:publication_document', this.publicationDocumentChanged);
      this.listenTo(this.model, 'change:publication_date change:publication_name change:publication_number',
                    _.debounce(this.publicationChanged, 1000));

      this.model.updateFrbrUri();
      this.stickit();
      this.repealChanged();
      this.commencingWorkChanged();
      this.parentChanged();
      this.publicationChanged();
      this.publicationDocumentChanged();
      if (!this.model.get('commencement_date')) {
        this.commencementDateUnknown.checked = true;
        this.commencementDateUnknownChanged();
      }
    },

    updatePageTitle: function() {
      if (this.model.get('title')) {
        document.title = this.model.get('title') + ' – Indigo';
      } else {
        document.title = 'New work – Indigo';
      }
      this.$('.work-title').text(this.model.get('title') || '(untitled work)');
      this.$('.work-frbr-uri').text(this.model.get('frbr_uri'));
    },

    numberChanged: function(model, value, options) {
      model.set('number', value.replace(/[^a-z\d-]+/gi, '-').replace(/--+/g, '-'));
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

    deleteRepeal: function(e) {
      e.preventDefault();
      this.model.set('repealed_by', null);
    },

    changeRepeal: function() {
      var chooser = new Indigo.WorkChooserView({
            country: this.model.get('country'),
            locality: this.model.get('locality') || '-',
          }),
          self = this;

      if (this.model.get('repealed_by')) {
        chooser.choose(Indigo.works.get(this.model.get('repealed_by')));
      }
      chooser.showModal().done(function(chosen) {
        if (chosen) {
          self.model.set('repealed_by', chosen);
          self.model.set('repealed_date', chosen.get('commencement_date') || chosen.get('publication_date'));
        }
      });
    },

    repealChanged: function() {
      var repealed_by = this.model.get('repealed_by');

      if (repealed_by) {
        this.$el.addClass('is-repealed');
        this.$('.work-repeal-view').html(this.workRepealTemplate({
          repealed_by: repealed_by.toJSON(),
        }));
        this.$('#id_work-repealed_date').attr('required', 'required');
      } else {
        this.$el.removeClass('is-repealed');
        this.$('.work-repeal-view').html(this.workRepealTemplate({}));
        this.$('#id_work-repealed_date').removeAttr('required');
      }
    },

    deleteCommencingWork: function(e) {
      e.preventDefault();
      this.model.set('commencing_work', null);
    },

    changeCommencingWork: function() {
      var chooser = new Indigo.WorkChooserView({
            country: this.model.get('country'),
            locality: this.model.get('locality') || '-',
          }),
          self = this;

      if (this.model.get('commencing_work')) {
        chooser.choose(Indigo.works.get(this.model.get('commencing_work')));
      }
      chooser.showModal().done(function(chosen) {
        if (chosen) {
          self.model.set('commencing_work', chosen);
        }
      });
    },

    commencedChanged: function() {
      if (this.model.get('commenced')) {
        this.$('#commencement_details').removeClass('d-none');
        this.commencementDateUnknown.checked = false;
        this.commencementDateUnknownChanged();
      } else {
        this.model.set('commencement_date', null);
        this.model.set('commencing_work', null);
        this.$('#commencement_details').addClass('d-none');
      }
    },

    commencementDateUnknownChanged: function() {
      this.$('#id_work-commencement_date').attr('disabled', this.commencementDateUnknown.checked);
      if (this.commencementDateUnknown.checked) {
        this.model.set('commencement_date', null);
      }
    },

    commencingWorkChanged: function() {
      var commencing_work = this.model.get('commencing_work');

      if (commencing_work) {
        this.$('.work-commencing-work').html(this.commencingWorkTemplate({
          commencing_work: commencing_work.toJSON(),
        }));
      } else {
        this.$('.work-commencing-work').html(this.commencingWorkTemplate({}));
      }
    },

    changeParent: function() {
      var chooser = new Indigo.WorkChooserView({
            country: this.model.get('country'),
            locality: this.model.get('locality') || '-',
          }),
          self = this;

      if (this.model.get('parent_work')) {
        chooser.choose(this.model.get('parent_work'));
      }
      chooser.showModal().done(function(chosen) {
        if (chosen) {
          self.model.set('parent_work', chosen);
        }
      });
    },

    deleteParent: function(e) {
      e.preventDefault();
      this.model.set('parent_work', null);
    },

    parentChanged: function() {
      if (this.model.get('parent_work')) {
        var parent = this.model.get('parent_work');

        this.$('#work_parent_work')
          .show('hidden')
          .find('.work_parent_title')
            .text(parent.get('title'))
            .attr('href', '/works' + parent.get('frbr_uri') + '/')
            .end()
          .find('.work_parent_uri')
            .text(parent.get('frbr_uri'));
      } else {
        this.$('#work_parent_work').hide();
      }
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
