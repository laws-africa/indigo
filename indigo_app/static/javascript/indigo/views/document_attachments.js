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
      this.document = options.document;
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
   * Handle the document attachments view.
   */
  Indigo.DocumentAttachmentsView = Backbone.View.extend({
    el: '.document-attachments-view',
    template: '#attachments-template',
    events: {
      'click .edit-attachment': 'editAttachment',
      'click .delete-attachment': 'deleteAttachment',
      'change [type=file]': 'fileSelected',
    },

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());
      this.document = options.document;
      this.dirty = false;
      this.deleted = [];

      this.model = new Indigo.AttachmentList(null, {document: this.document});
      this.model.on('change add remove reset saved', this.render, this);
      this.model.on('change add remove', this.setDirty, this);
      this.model.on('saved', this.setClean, this);
      this.model.fetch({reset: true});

      this.box = new Indigo.AttachmentEditorView({document: this.document});

      this.stickit();
    },

    render: function() {
      var self = this;
      var models = this.model.toJSON();
      var count = models.length;

      _.each(models, function(m) {
        m.prettySize = self.prettySize(m.size);
      });

      this.$el.find('.document-attachments-list').html(this.template({
        attachments: models,
      }));

      // update attachment count in nav tabs
      $('.sidebar .nav .attachment-count').text(count === 0 ? '' : count);
    },

    editAttachment: function(e) {
      e.preventDefault();

      var index = $(e.target).closest('tr').data('index');
      this.box.show(this.model.at(index));
    },

    deleteAttachment: function(e) {
      e.preventDefault();

      var index = $(e.target).closest('tr').data('index');
      var attachment = this.model.at(index);

      if (confirm("Really delete this attachment?")) {
        // this will be deleted on the server during save()
        this.deleted.push(attachment);

        // save the URL, which is derived from the collection, before we remove
        // it from the collection
        attachment.url = attachment.url();
        this.model.remove(attachment);
      }
    },

    fileSelected: function(e) {
      var self = this;

      _.each(e.originalEvent.target.files, function(f) {
        self.attachFile(f);
      });
    },

    attachFile: function(file) {
      // We use the FormData interface which is supported in all decent
      // browsers and IE 10+.
      //
      // https://developer.mozilla.org/en-US/docs/Web/Guide/Using_FormData_Objects

      this.model.add({
        filename: file.name,
        size: file.size,
        mime_type: file.type,
        file: file,
      });
    },
    
    save: function(force) {
      // TODO: validation
      var self = this;

      // don't do anything if it hasn't changed
      if (!this.dirty && !force) {
        return $.Deferred().resolve();
      }

      return $
        .when.apply($, this.deleted.map(function(attachment) {
          return attachment.destroy();
        }))
        .then(function() {
          self.deleted = [];
          return self.model.save();
        });
    },

    setDirty: function() {
      if (!this.dirty) {
        this.dirty = true;
        this.trigger('dirty');
      }
    },

    setClean: function() {
      if (this.dirty) {
        this.dirty = false;
        this.trigger('clean');
      }
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
