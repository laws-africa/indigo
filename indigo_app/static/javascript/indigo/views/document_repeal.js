(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

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
    },

    render: function() {
      this.$el.html(this.template({
        repeal: this.model.get('repeal')
      }));
    },

    changeRepeal: function(e) {
      e.preventDefault();

      var repeal = this.model.get('repeal'),
          document = this.model,
          item;
      var chooser = new Indigo.DocumentChooserView({
        noun: 'repeal',
        verb: 'repealing',
      });

      repeal = repeal ?  new Backbone.Model(repeal) : null;

      if (repeal && repeal.get('repealing_uri')) {
        // find the document the model corresponds to
        item = chooser.collection.findWhere({frbr_uri: repeal.get('repealing_uri')});
      }
      if (!item && repeal) {
        item = Indigo.Document.newFromFrbrUri(repeal.get('repealing_uri'));
        item.set({
          expression_date: repeal.get('date'),
          title: repeal.get('repealing_title'),
        });
      }

      chooser.setFilters({country: this.model.get('country')});
      chooser.choose(item);
      chooser.showModal().done(function(chosen) {
        if (chosen) {
          document.set('repeal', {
            date: chosen.get('expression_date'),
            repealing_title: chosen.get('title'),
            repealing_uri: chosen.get('frbr_uri'),
            repealing_id: chosen.get('id'),
          });
        }
      });
    },

    deleteRepeal: function(e) {
      if (confirm("Really mark this document is NOT repealed?")) {
        this.model.set('repeal', null);
      }
    },
  });
})(window);
