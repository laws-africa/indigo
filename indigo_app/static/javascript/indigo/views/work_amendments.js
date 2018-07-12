(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.EditWorkAmendmentView = Backbone.View.extend({
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
      this.$el.html(this.template(amendment));
    },

    save: function() {
      this.originalModel.set(this.model.attributes);
      this.deferred.resolve();
    },

    cancel: function() {
      this.deferred.reject();
    },
  });

  /**
   * Handle the work amendments display.
   */
  Indigo.WorkAmendmentsView = Backbone.View.extend({
    el: '#work-amendments-view',
    template: '#work-amendments-template',
    events: {
      'click .save-work': 'save',
      'click .add-amendment': 'addAmendment',
      'click .edit-amendment': 'editAmendment',
      'click .delete-amendment': 'deleteAmendment',
      'click .create-expression': 'createExpression',
    },

    initialize: function() {
      this.template = Handlebars.compile($(this.template).html());

      this.model = new Indigo.Work(Indigo.Preloads.work);
      this.deleted = new Indigo.WorkAmendmentCollection([], {work: this.model});
      this.documents = new Indigo.Library(Indigo.Preloads.documents, {country: this.model.get('country')});

      this.collection = new Indigo.WorkAmendmentCollection(Indigo.Preloads.amendments, {
        work: this.model,
        parse: true,
        comparator: function(a, b) {
          // most recent first
          return -(a.get('date') || '').localeCompare(b.get('date'));
        },
      });
      this.listenTo(this.collection, 'add remove change sort', this.render);
      this.listenTo(this.collection, 'add remove change', this.setDirty);
      this.listenTo(this.collection, 'sync', this.setClean);

      this.render();
      this.canSave();
    },

    render: function() {
      var amendments = this.collection.toJSON(),
          self = this;

      // pull in documents
      amendments.forEach(function(a) {
        a.documents = _.map(self.documents.where({expression_date: a.date}), function(a) { return a.toJSON(); });
      });

      amendments.push({
        initial: true,
        date: this.model.get('publication_date'),
        documents: _.map(self.documents.where({expression_date: this.model.get('publication_date')}), function(a) { return a.toJSON(); }),
      });

      this.$('.work-amendments').html(this.template({
        amendments: amendments,
        readonly: Indigo.user.hasPerm('indigo_api.can_change_amendment'),
        work: this.model.toJSON(),
      }));
    },

    addAmendment: function(e) {
      e.preventDefault();

      var chooser = new Indigo.WorkChooserView({}),
          self = this;

      chooser.setFilters({country: this.model.get('country')});
      chooser.showModal().done(function(chosen) {
        if (chosen) {
          self.collection.add(new Indigo.WorkAmendment({
            amending_work: chosen,
            date: chosen.get('commencement_date') || chosen.get('publication_date'),
          }));
        }
      });
    },

    editAmendment: function(e) {
      e.preventDefault();

      var index = $(e.target).data('index'),
          $item = $(e.target).closest('li'),
          amendment = this.collection.at(index),
          $container = $item.find('.edit-wrapper'),
          self = this;

      var editor = new Indigo.EditWorkAmendmentView({
        model: amendment,
        country: this.model.get('country'),
      });
      editor.show()
        .done(function() {
          self.collection.sort();
        })
        .always(function() {
          editor.remove();
        });

      $container.append(editor.el);
    },

    deleteAmendment: function(e) {
      e.preventDefault();

      var index = $(e.target).data('index');
      var amendment = this.collection.at(index);

      if (confirm("Really delete this amendment?")) {
        this.collection.remove(amendment);
        if (!amendment.isNew()) this.deleted.add(amendment);
      }
    },

    createExpression: function(e) {
      e.preventDefault();

      // create an amended version of this document at a particular date
      var date = $(e.target).data('date');

      if (confirm('Create a new amended versiot at ' + date + '? Unsaved changes will be lost!')) {
        Indigo.progressView.peg();

        $.post(this.model.url() + '/expressions_at?date=' + date)
          .done(function(doc) {
            document.location = '/documents/' + doc.id + '/';
          })
          .fail(function() {
            Indigo.progressView.unpeg();
          });
      }
    },

    save: function() {
      this.deleted.invoke('destroy');
      this.deleted.reset([]);
      this.collection.invoke('save');
    },

    canSave: function() {
      this.$('.btn.save-work').attr('disabled', !this.dirty);
    },

    setDirty: function() {
      this.dirty = true;
      this.canSave();
    },

    setClean: function() {
      this.dirty = false;
      this.canSave();
    },

    isDirty: function(e) {
      return this.dirty;
    },

  });
})(window);
