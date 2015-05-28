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
    },

    show: function(model) {
      this.isNew = !model;
      this.originalModel = model;

      if (model) {
        // clone the amendment and edit the clone
        this.model = model.clone();
      } else {
        this.model = new Indigo.Amendment();
      }

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

      this.document.trigger('change change:amendments');
      this.$el.modal('hide');
    },
    
    dismiss: function() {
      this.unstickit();
      this.model = null;
      this.originalModel = null;
    },
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
    el: '.amendments-container',
    template: '#amendments-template',
    events: {
      'click .add-amendment': 'addAmendment',
      'click .edit-amendment': 'editAmendment',
      'click .delete-amendment': 'deleteAmendment',
    },

    initialize: function() {
      this.template = Handlebars.compile($(this.template).html());

      this.model.on('change:amendments', this.render, this);

      this.box = new Indigo.AmendmentView({model: null, document: this.model});

      this.stickit();
    },

    render: function() {
      var target = this.$el.find('.amendment-list');

      if (this.model.get('amendments')) {
        target.html(this.template({
          amendments: this.model.get('amendments').toJSON(),
        }));
      } else {
        target.html('');
      }
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
