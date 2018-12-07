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
      this.country = Indigo.Preloads.country_code;
      this.locality = Indigo.Preloads.locality_code;

      this.documents = new Indigo.Library({
        comparator: function(a, b) {
          // most recent expression first
          return -(a.get('expression_date') || '').localeCompare(b.get('expression_date'));
        },
      });
      this.documents.params.country = this.country;
      this.documents.params.locality = this.locality;

      this.listenTo(this.model, 'change:work', this.workChanged);
      this.listenTo(this.model, 'change', this.render);
      this.listenTo(this.documents, 'reset', this.render);

      this.stickit();
      this.workChanged();
      this.render();
    },

    workChanged: function() {
      if (this.model.get('work')) {
        this.documents.setParams({frbr_uri: this.model.get('work').get('frbr_uri')});
      } else {
        this.documents.reset([]);
      }
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

      if (this.documents.length > 0) {
        this.$('.document-details').show();
      } else {
        this.$('.document-details').hide();
      }

      var $select = $('#id_document').empty();
      var opt = document.createElement('option');
      opt.innerText = '(none)';
      opt.setAttribute('value', '');
      opt.selected = !model.document;
      $select.append(opt);

      this.documents.each(function(doc) {
        var opt = document.createElement('option');
        opt.setAttribute('value', doc.get('id'));
        opt.innerText = '@ ' + doc.get('expression_date') + ' · ' + doc.get('language');
        opt.selected = doc.get('id') == (model.document ? model.document.id : null);
        $select.append(opt);
      });
    },
  });
})(window);
