(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /** This handles editing of a document attachment.
   */
  Indigo.AttachmentEditorView = Backbone.View.extend({
    el: '#attachment-box',
    events: {
      'hidden.bs.modal': 'dismiss',
      'click .btn.save': 'save',
    },
    bindings: {
      '#attachment_filename': 'filename',
      '#attachment_size': 'size',
      '#attachment_mime_type': 'mime_type',
    },

    initialize: function(options) {
    },

    show: function(model) {
      this.originalModel = model;
      this.model = model.clone();

      this.stickit();

      this.$el.modal('show');
    },

    save: function(e) {
      this.originalModel.set(this.model.attributes);
      this.$el.modal('hide');
    },
    
    dismiss: function() {
      this.unstickit();
      this.model = null;
      this.originalModel = null;
    }
  });

  /**
   * Handle the document repeal view.
   */
  Indigo.DocumentAttachmentsView = Backbone.View.extend({
    el: '.document-attachments-view',
    template: '#attachments-template',
    events: {
      'click .edit-attachment': 'editAttachment',
      'click .delete-attachment': 'deleteAttachment',
    },

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());
      this.model = new Indigo.AttachmentList();
      this.model.url = options.document.url() + '/attachments';
      this.model.on('change sync', this.render, this);
      this.model.fetch();

      // TODO: let parent know this is dirty

      this.box = new Indigo.AttachmentEditorView({document: this.model});

      this.stickit();
    },

    render: function() {
      var self = this;
      var models = this.model.toJSON();

      _.each(models, function(m) {
        m.prettySize = self.prettySize(m.size);
      });

      this.$el.find('.document-attachments-list').html(this.template({
        attachments: models,
      }));
    },

    editAttachment: function(e) {
      e.preventDefault();

      var index = $(e.target).closest('tr').data('index');
      this.box.show(this.model.at(index));
    },

    deleteAttachment: function(e) {
      // TODO
    },
    
    save: function() {
      // TODO:
    },

    prettySize: function(bytes) {
      var i = -1;
      var byteUnits = [' kB', ' MB', ' GB', ' TB', 'PB', 'EB', 'ZB', 'YB'];

      do {
        bytes = bytes / 1024;
        i++;
      } while (bytes > 1024);

      return Math.max(bytes, 0.1).toFixed(1) + byteUnits[i];
    }
  });
})(window);
