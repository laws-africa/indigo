(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.EditWorkAmendmentView = Backbone.View.extend({
    tagName: 'tr',
    template: '#amendment-editor-template',
    events: {
      'click .save-amendment': 'save',
      'click .cancel': 'cancel',
    },
    bindings: {
      '.amendment-date': 'date',
    },

    initialize: function(options) {
      this.originalModel = this.model;
      this.model = this.originalModel.clone();

      this.country = options.country;
      this.template = Handlebars.compile($(this.template).html());

      this.render();
      this.stickit();
    },

    show: function() {
      this.deferred = $.Deferred();
      return this.deferred;
    },

    render: function() {
      var amendment = this.model.toJSON();
      amendment.work = amendment.work.toJSON();
      this.$el.html(this.template(amendment));
    },

    save: function() {
      this.originalModel.set(this.model.attributes);
      this.deferred.resolve();
    },

    cancel: function() {
      this.deferred.resolve();
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
  Indigo.WorkAmendmentsView = Backbone.View.extend({
    el: '#work-amendments-view',
    template: '#work-amendments-template',
    events: {
      'click .save-work': 'save',
      'click .add-amendment': 'addAmendment',
      'click .edit-amendment': 'editAmendment',
      'click .delete-amendment': 'deleteAmendment',
    },

    initialize: function() {
      this.template = Handlebars.compile($(this.template).html());

      this.model = new Indigo.Work(Indigo.Preloads.work);
      this.deleted = new Backbone.Collection();

      // TODO: load from preloads
      this.collection = new Backbone.Collection([], {
        comparator: function(a, b) {
          // most recent first
          return -(a.get('date') || '').localeCompare(b.get('date'));
        },
      });
      this.collection.url = this.model.url() + '/amendments';
      this.listenTo(this.collection, 'add remove change', this.render);

      this.render();
    },

    render: function() {
      var amendments = this.collection.toJSON();
      amendments.forEach(function(a) {
        a.work = a.work.toJSON();
      });

      this.$('.work-amendments').html(this.template({
        amendments: amendments,
      }));
    },

    addAmendment: function(e) {
      e.preventDefault();

      var chooser = new Indigo.WorkChooserView({}),
          self = this;

      chooser.setFilters({country: this.model.get('country')});
      chooser.showModal().done(function(chosen) {
        if (chosen) {
          // TODO: uri for amending doc may not be unique
          self.collection.add(new Backbone.Model({
            work: chosen,
            date: chosen.get('publication_date'),
          }));
        }
      });
    },

    editAmendment: function(e) {
      e.preventDefault();

      var $row = $(e.target).closest('tr'),
          index = $row.data('index'),
          amendment = this.collection.at(index);

      var editor = new Indigo.EditWorkAmendmentView({
        model: amendment,
        country: this.model.get('country'),
      });
      editor.show().always(function() {
        editor.remove();
        $row.show();
      });

      $row.hide();
      editor.$el.insertAfter($row);
    },

    deleteAmendment: function(e) {
      e.preventDefault();

      var index = $(e.target).closest('tr').data('index');
      var amendment = this.collection.at(index);

      if (confirm("Really delete this amendment?")) {
        this.collection.remove(amendment);
        if (!amendment.isNew()) this.deleted.add(amendment);
      }
    },

    save: function() {
      this.deleted.invoke('destroy');
      this.deleted.reset([]);
      this.collection.invoke('save');
    },

  });
})(window);
