(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /** This handles editing of a document's repeal details.
   */
  Indigo.RepealEditorView = Backbone.View.extend({
    el: '#repeal-box',
    events: {
      'hidden.bs.modal': 'dismiss',
      'click .btn.save': 'save',
    },
    bindings: {
      '#repeal_date': 'date',
      '#repeal_title': 'repealing_title',
      '#repeal_uri': 'repealing_uri',
    },

    initialize: function(options) {
      this.document = options.document;
      this.chooser = new Indigo.DocumentChooserView({el: this.$el.find('.document-chooser')});
      this.chooser.on('chosen', this.chosen, this);
    },

    show: function() {
      var repealing_doc = null;

      this.model = new Backbone.Model(this.document.get('repeal'));

      // find the document the model corresponds to
      if (this.model.get('amending_uri')) {
        repealing_doc = this.chooser.model.findWhere({frbr_uri: this.model.get('amending_uri')});
      }

      this.chooser.setFilters({country: this.document.get('country')});
      this.chooser.choose(repealing_doc);

      this.stickit();

      this.$el.modal('show');
    },

    save: function(e) {
      this.document.set('repeal', this.model.toJSON());
      this.$el.modal('hide');
    },
    
    dismiss: function() {
      this.unstickit();
      this.model = null;
    },

    chosen: function() {
      // user chose a new item in the document chooser
      var chosen = this.chooser.chosen;
      if (chosen) {
        this.model.set({
          date: chosen.get('expression_date'),
          repealing_title: chosen.get('title'),
          repealing_uri: chosen.get('frbr_uri'),
          repealing_id: chosen.get('id'),
        });
      }
    }
  });

  /**
   * Handle the document repeal view.
   */
  Indigo.DocumentRepealView = Backbone.View.extend({
    el: '.document-repeal-view',
    template: '#repeal-template',
    events: {
      'click .change-repeal': 'changeRepeal',
      'click .delete-repeal': 'deleteRepeal',
    },

    initialize: function() {
      this.template = Handlebars.compile($(this.template).html());

      this.model.on('change:repeal sync', this.render, this);

      this.box = new Indigo.RepealEditorView({document: this.model});

      this.stickit();
    },

    render: function() {
      this.$el.html(this.template({
        repeal: this.model.get('repeal')
      }));
    },

    changeRepeal: function(e) {
      e.preventDefault();
      this.box.show();
    },

    deleteRepeal: function(e) {
      if (confirm("Really mark this document is NOT repealed?")) {
        this.model.set('repeal', null);
      }
    },
  });
})(window);
