(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * This handles editing a single document attachment.
   */
  Indigo.AttachmentEditorView = Backbone.View.extend({
    template: '#edit-attachment-template',
    events: {
      'submit form': 'save',
      'click .btn.cancel': 'cancel',
    },

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());
      this.render();
    },

    render: function() {
      this.$el.html(this.template());
      this.$('input').val(this.model.get('filename'));
    },

    show: function(model) {
      this.deferred = $.Deferred();
      return this.deferred;
    },

    save: function(e) {
      this.model.set('filename', this.$('input').val());
      this.deferred.resolve();
    },
    
    cancel: function() {
      this.deferred.reject();
    }
  });

  /**
   * This handles listing and choosing document attachments.
   */
  Indigo.AttachmentListView = Backbone.View.extend({
    template: '#attachments-template',
    events: {
      'click .edit-attachment': 'editAttachment',
      'click .delete-attachment': 'deleteAttachment',
      'click .add-attachment .btn': 'addAttachment',
      'click .attachments-list > li': 'attachmentClicked',
      'click .wrapper > a': 'attachmentClicked',
      'dragleave': 'noDrag',
      'dragover': 'dragover',
      'drop': 'drop',
      'change [type=file]': 'fileUploaded',
    },

    ICONS: {
      'application/pdf': 'fa-file-pdf',
      'application/msword': 'fa-file-word',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'fa-file-word',
    },

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());
      this.filter = options.filter;
      this.selectable = !!options.selectable;

      this.model.on('change add remove reset saved', this.render, this);
    },

    selectItem: function(model) {
      this.selectedItem = model;
      this.trigger('selectionChanged', this.selectedItem);
      this.render();
    },

    render: function() {
      var self = this;
      var models = this.model.toJSON();
      var count = models.length;

      if (this.filter) models = models.filter(this.filter);

      _.each(models, function(m) {
        m.prettySize = Indigo.formatting.prettyFileSize(m.size);
        m.isImage = m.mime_type.startsWith('image/');
        m.icon = self.ICONS[m.mime_type] || 'fa-file-o';
        m.selected = self.selectedItem && self.selectedItem.get('id') == m.id;
      });

      this.$el.html(this.template({
        attachments: models,
        selectable: this.selectable,
      }));
    },

    editAttachment: function(e) {
      e.preventDefault();

      var $li = $(e.target).closest('li'),
          index = $li.data('index'),
          attachment = this.model.at(index),
          editor;

      editor = new Indigo.AttachmentEditorView({
        model: attachment,
      });
      editor.show()
        .always(function() {
          editor.remove();
          $li.find('.attachment-details, .buttons').show();
        });

      $li.find('.attachment-details, .buttons').hide();
      $li.find('.attachment-details').after(editor.el);
    },

    addAttachment: function(e) {
      this.$('input[type=file]').click();
    },

    deleteAttachment: function(e) {
      e.preventDefault();

      var index = $(e.target).closest('li').data('index');
      var attachment = this.model.at(index);

      if (confirm("Really delete this attachment?")) {
        // save the URL, which is derived from the collection, before we remove
        // it from the collection
        attachment.url = attachment.url();
        this.model.remove(attachment);
      }
    },

    fileUploaded: function(e) {
      _.forEach(e.originalEvent.target.files, _.bind(this.attachFile, this));
    },

    attachFile: function(file) {
      // We use the FormData interface which is supported in all decent
      // browsers and IE 10+.
      //
      // https://developer.mozilla.org/en-US/docs/Web/Guide/Using_FormData_Objects

      this.model.add({
        filename: file.name.replaceAll(' ', '_'),
        size: file.size,
        mime_type: file.type,
        file: file,
      }).save();
    },

    attachmentClicked: function(e) {
      if (this.selectable && !$(e.target).closest('li').hasClass('add-attachment')) {
        e.preventDefault();
        var $item = $(e.currentTarget);

        this.$el.find('.selected').not($item).removeClass('selected');
        $item.toggleClass('selected');

        if ($item.hasClass("selected")) {
          this.selectedItem = this.model.get($item.data('id'));
        } else {
          this.selectedItem = null;
        }

        this.trigger('selectionChanged', this.selectedItem);
      }
    },

    dragover: function(e) {
      e.stopPropagation();
      e.preventDefault();
      e.originalEvent.dataTransfer.dropEffect = 'copy';
      this.$('.add-attachment').addClass('incoming');
    },

    noDrag: function() {
      this.$('.add-attachment').removeClass('incoming');
    },

    drop: function(e) {
      e.stopPropagation();
      e.preventDefault();
      this.$('.add-attachment').removeClass('incoming');

      _.forEach(e.originalEvent.dataTransfer.files, _.bind(this.attachFile, this));
    },
  });

  /**
   * Handle the document attachments view, a wrapper around an AttachmentListView.
   */
  Indigo.DocumentAttachmentsView = Backbone.View.extend({
    el: '.document-attachments-view',

    initialize: function(options) {
      this.document = options.document;
      this.dirty = false;
      this.deleted = [];

      this.model = this.document.attachments();
      this.model.on('change add remove', this.setDirty, this);
      this.model.on('saved', this.setClean, this);
      this.model.on('remove', this.attachmentRemoved, this);

      this.listView = new Indigo.AttachmentListView({
        model: this.model,
        el: this.$('.document-attachments-list')[0],
      });
    },

    attachmentRemoved: function(model) {
      // this will be deleted on the server during save()
      this.deleted.push(model);
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
  });

  /**
   * This handles inserting/editing an image based on the list of document attachments.
   * It's triggered from the document editor view.
   */
  Indigo.InsertImageView = Backbone.View.extend({
    el: '#insert-image-modal',
    events: {
      'click .btn.save': 'save',
    },

    initialize: function(options) {
      this.model = options.document.attachments();
      this.callback = options.callback;
      this.selectedItem = null;
      this.listView = new Indigo.AttachmentListView({
        model: this.model,
        el: this.$('.image-list-holder')[0],
        selectable: true,
        filter: function(a) {
          return a.mime_type.startsWith('image/');
        }
      });

      this.listenTo(this.listView, 'selectionChanged', this.selectionChanged);
    },

    show: function(callback, selectedItem) {
      this.selectedItem = selectedItem;
      this.callback = callback;
      this.listView.selectItem(this.selectedItem);
      this.$el.modal('show');
    },

    selectionChanged: function(selection) {
      this.$('.save').prop('disabled', selection === null);
    },

    save: function(e) {
      this.$el.modal('hide');
      if (this.listView.selectedItem) {
        this.callback(this.listView.selectedItem);
      }
    },
  });
})(window);
