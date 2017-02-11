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
      this.collection = options.collection;
      this.chooser = new Indigo.DocumentChooserView({el: this.$('.document-chooser')});
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
        this.collection.add(this.model);
      } else {
        this.originalModel.set(this.model.attributes);
      }

      // TODO: we're not actually editing this doc's amendments, but the expressionSet's amendments
      // so, we should be updating THAT collection of amendments and the expressionSet is responsible
      // for adjusting all documents as necessary
      // this.document.get('amendments').sort();
      // this.document.trigger('change change:amendments');
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
    amendmentExpressionsTemplate: '#amendment-expressions-template',
    events: {
      'click .add-amendment': 'addAmendment',
      'click .edit-amendment': 'editAmendment',
      'click .delete-amendment': 'deleteAmendment',
      'click .create-expression': 'createExpression',
    },

    initialize: function() {
      this.amendmentExpressionsTemplate = Handlebars.compile($(this.amendmentExpressionsTemplate).html());

      this.model.on('change:amendments', this.render, this);
      this.model.on('change:frbr_uri', this.frbrChanged, this);

      this.listenTo(this.model.expressionSet, 'add remove reset change', this.render);
      this.listenTo(this.model.expressionSet.amendments, 'change add remove reset', this.render);

      this.box = new Indigo.AmendmentView({model: null, document: this.model, collection: this.model.expressionSet.amendments});

      this.render();
    },

    render: function() {
      var self = this;
      var document_id = this.model.get('id');
      var dates = this.model.expressionSet.allDates(),
          pubDate = this.model.expressionSet.initialPublicationDate();

      // build up a view of amended expressions
      var amended_expressions = _.map(dates, function(date) {
        var doc = self.model.expressionSet.atDate(date);
        var info = {
          date: date,
          document: doc && doc.toJSON(),
          current: doc && doc.get('id') == document_id,
          amendments: _.map(self.model.expressionSet.amendmentsAtDate(date), function(a) { return a.toJSON(); }),
          initial: date == pubDate,
        };
        info.linkable = info.document && !info.current;

        return info;
      });

      this.$('.amendment-expressions').html(this.amendmentExpressionsTemplate({
        amended_expressions: amended_expressions,
      }));

      // update amendment count in nav tabs
      $('.sidebar .nav .amendment-count').text(this.model.expressionSet.length === 0 ? '' : this.model.expressionSet.length);
    },

    addAmendment: function(e) {
      e.preventDefault();
      this.box.show(null);
    },

    editAmendment: function(e) {
      e.preventDefault();

      var uri = $(e.target).closest('li').data('uri');
      var amendment = this.model.expressionSet.amendments.findWhere({amending_uri: uri});

      this.box.show(amendment);
    },

    deleteAmendment: function(e) {
      e.preventDefault();

      var uri = $(e.target).closest('li').data('uri');
      var amendment = this.model.expressionSet.amendments.findWhere({amending_uri: uri});

      if (confirm("Really delete this amendment?")) {
        this.model.expressionSet.amendments.remove(amendment);
      }
    },

    createExpression: function(e) {
      e.preventDefault();

      // create an amended version of this document at a particular date
      var date = $(e.target).data('date');

      if (confirm('Create a new amended versiot at ' + date + '? Unsaved changes will be lost!')) {
        Indigo.progressView.peg();
        this.model.expressionSet.createExpressionAt(date).done(function(doc) {
          document.location = '/documents/' + doc.get('id') + '/';
        });
      }
    },

  });
})(window);
