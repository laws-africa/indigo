(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /** This handles editing and creation of Amendment instances.
   */
  Indigo.AmendmentView = Backbone.View.extend({
    el: '#amendment-box',
    events: {
      'hidden.bs.modal': 'dismiss',
      'click .btn.save': 'save',
    },
    bindings: {
      '#amendment_date': 'date',
      '#amendment_title': 'amending_title',
      '#amendment_uri': 'amending_uri',
    },

    initialize: function(options) {
      this.document = options.document;
      this.chooser = new Indigo.DocumentChooserView({el: this.$el.find('.document-chooser')});
      this.chooser.on('chosen', this.chosen, this);
    },

    show: function(model) {
      var amending_doc = null;

      this.isNew = !model;
      this.originalModel = model;

      if (model) {
        // clone the amendment and edit the clone
        this.model = model.clone();
        // find the document the model corresponds to
        amending_doc = this.chooser.model.findWhere({frbr_uri: this.model.get('amending_uri')});
      } else {
        this.model = new Indigo.Amendment();
      }

      this.chooser.setFilters({country: this.document.get('country')});
      this.chooser.choose(amending_doc);

      this.stickit();

      this.$el.modal('show');
    },

    save: function(e) {
      if (this.isNew) {
        this.document.get('amendments').add(this.model);
      } else {
        this.originalModel.attributes = _.clone(this.model.attributes);
        this.originalModel.trigger('change');
      }

      this.document.get('amendments').sort();
      this.document.trigger('change change:amendments');
      this.$el.modal('hide');
    },
    
    dismiss: function() {
      this.unstickit();
      this.model = null;
      this.originalModel = null;
    },

    chosen: function() {
      // user chose a new item in the document chooser
      var chosen = this.chooser.chosen;
      if (chosen) {
        this.model.set({
          date: chosen.get('expression_date'),
          amending_title: chosen.get('title'),
          amending_uri: chosen.get('frbr_uri'),
          amending_id: chosen.get('id'),
        });
      }
    }
  });

  /**
   * Handle the document amendments display.
   *
   * Note that the amendments attribute of the document might
   * be changed outside of this view, in particular it could become
   * a new AmendmentList collection. That means we can't attach
   * event handlers, so the views above (and ours) must trigger
   * events on the owning document itself, not just the AmendmentList
   * collection.
   */
  Indigo.DocumentAmendmentsView = Backbone.View.extend({
    el: '.document-amendments-view',
    amendmentsTemplate: '#amendments-template',
    amendedVersionsTemplate: '#amended-versions-template',
    events: {
      'click .add-amendment': 'addAmendment',
      'click .edit-amendment': 'editAmendment',
      'click .delete-amendment': 'deleteAmendment',
    },

    initialize: function() {
      this.amendmentsTemplate = Handlebars.compile($(this.amendmentsTemplate).html());
      this.amendedVersionsTemplate = Handlebars.compile($(this.amendedVersionsTemplate).html());

      this.model.on('change:amendments sync', this.render, this);

      this.box = new Indigo.AmendmentView({model: null, document: this.model});

      this.stickit();
    },

    render: function() {
      var count = 0;
      var document_id = this.model.get('id');
      var amendments = this.model.get('amendments').toJSON();

      if (amendments.length > 0) {
        count = amendments.length;

        // link in the amended versions
        _.each(this.model.get('amended_versions') || [], function(version) {
          _.each(amendments, function(a) {
            if (a.date == version.expression_date) {
              if (version.id == document_id) {
                // it's this version
                a.this_document = true;
              } else {
                a.amended_id = version.id;
              }
            }
          });
        });
      }
      this.$el.find('.amendments-list').html(this.amendmentsTemplate({
        amendments: amendments,
      }));

      // update amendment count in nav tabs
      $('.sidebar .nav .amendment-count').text(count === 0 ? '' : count);

      // amended versions
      var amended_versions = _.map(this.model.get('amended_versions'), function(v) {
        v = _.clone(v);
        if (v.id == document_id) {
          v.this_document = true;
        }
        return v;
      });

      this.$el.find('.amended-versions-list').html(this.amendedVersionsTemplate({
        amended_versions: amended_versions,
      }));
    },

    addAmendment: function(e) {
      e.preventDefault();
      this.box.show(null);
    },

    editAmendment: function(e) {
      e.preventDefault();

      var index = $(e.target).closest('tr').data('index');
      var amendment = this.model.get('amendments').at(index);

      this.box.show(amendment);
    },

    deleteAmendment: function(e) {
      e.preventDefault();

      var index = $(e.target).closest('tr').data('index');
      var amendment = this.model.get('amendments').at(index);

      if (confirm("Really delete this amendment?")) {
        this.model.get('amendments').remove(amendment);
        this.model.trigger('change change:amendments');
      }
    },

  });
})(window);
