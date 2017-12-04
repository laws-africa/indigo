(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

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
      $('.sidebar .nav .amendment-count').text(this.model.expressionSet.length <= 1 ? '' : this.model.expressionSet.length);
    },

    addAmendment: function(e) {
      e.preventDefault();

      var amendments = this.model.expressionSet.amendments;
      var chooser = new Indigo.DocumentChooserView({
        noun: 'amendment',
        verb: 'amending',
      });

      chooser.setFilters({country: this.model.get('country')});
      chooser.choose(null);
      chooser.showModal().done(function(chosen) {
        if (chosen) {
          amendments.add(new Indigo.Amendment({
            date: chosen.get('expression_date'),
            amending_title: chosen.get('title'),
            amending_uri: chosen.get('frbr_uri'),
            amending_id: chosen.get('id'),
          }));
        }
      });
    },

    editAmendment: function(e) {
      e.preventDefault();

      var uri = $(e.target).closest('li').data('uri');
      var amendment = this.model.expressionSet.amendments.findWhere({amending_uri: uri});
      var chooser = new Indigo.DocumentChooserView({
        noun: 'amendment',
        verb: 'amending',
      });

      chooser.setFilters({country: this.model.get('country')});
      // choose the document the model corresponds to
      chooser.choose(chooser.collection.findWhere({frbr_uri: amendment.get('amending_uri')}));
      chooser.showModal().done(function(chosen) {
        if (chosen) {
          amendment.set({
            date: chosen.get('expression_date'),
            amending_title: chosen.get('title'),
            amending_uri: chosen.get('frbr_uri'),
            amending_id: chosen.get('id'),
          });
        }
      });
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
