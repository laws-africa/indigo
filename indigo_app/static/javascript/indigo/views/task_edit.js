(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  function idOrNull(val) {
    return val ? val.get('id') : null;
  }

  /**
   * A view that lets a user create or edit a Task.
   *
   * This view supplements the actual HTML form on the work page
   * by filling in some fields such as the linked work and document.
   */
  Indigo.TaskEditView = Backbone.View.extend({
    el: '#edit-task-view',
    events: {
      'click .change-work': 'changeWork',
      'click .delete-work': 'deleteWork',
    },
    workTemplate: '#task-work-template',
    documentTemplate: '#task-document-template',
    bindings: {
      '#id_work': {
        observe: 'work',
        onGet: function(w) { return w ? w.get('id') : ''; },
      },
      '#id_document': {
        observe: 'document',
        onGet: function(d) { return d ? d.get('id') : ''; },
      },
    },

    initialize: function(options) {
      var work = Indigo.Preloads.work,
          document = Indigo.Preloads.document;

      if (work) work = new Indigo.Work(work);
      if (document) document = new Indigo.Document(document);

      this.model = new Backbone.Model({
        work: work,
        document: document,
      });
      this.workTemplate = Handlebars.compile($(this.workTemplate).html());
      this.documentTemplate = Handlebars.compile($(this.documentTemplate).html());
      this.country = Indigo.Preloads.country_code;
      this.locality = Indigo.Preloads.locality_code;
      this.listenTo(this.model, 'change', this.render);

      this.stickit();
      this.render();
    },

    deleteWork: function(e) {
      this.model.set({work: null, work_id: null});
    },

    changeWork: function() {
      var self = this,
          chooser = new Indigo.WorkChooserView({
            country: this.country,
            locality: this.locality || '-',
            disable_country: true,
            disable_locality: true,
          });

      if (this.model.get('work')) {
        chooser.choose(this.model.get('work'));
      }
      chooser.showModal().done(function(chosen) {
        if (chosen) {
          self.model.set({
            work: chosen,
            document: null,
          });
        }
      });
    },

    render: function() {
      var model = this.model.toJSON();
      model.work = model.work ? model.work.toJSON() : null;
      model.document = model.document ? model.document.toJSON() : null;

      this.$('.work-details').html(this.workTemplate(model));
      this.$('.document-details').html(this.documentTemplate(model));
    },
  });
})(window);
