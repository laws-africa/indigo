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
      this.$el.modal('hide');
    },
    
    dismiss: function() {
      this.unstickit();
      this.model = null;
      this.originalModel = null;
    },
  });

  // Handle the document amendments display
  Indigo.DocumentAmendmentsView = Backbone.View.extend({
    el: '.amendments-container',
    template: '#amendments-template',
    events: {
      'click .add-amendment': 'addAmendment',
    },

    initialize: function() {
      this.template = Handlebars.compile($(this.template).html());

      var amendments = this.model.get('amendments');
      if (amendments) {
        amendments = _.map(amendments, function(a) { return new Indigo.Amendment(a); });
      } else {
        amendments = [];
      }
      this.model.set('amendments', new Indigo.AmendmentList(amendments), {silent: true});

      this.model.on('change:amendments', this.render, this);
      this.model.get('amendments').on('change add remove', this.render, this);

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

  });
})(window);
