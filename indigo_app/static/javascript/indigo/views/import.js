(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.ImportView = Backbone.View.extend({
    el: '#import-document',
    events: {
      'click .btn.import': 'import',
    },

    initialize: function() {
      var self = this;

      this.$el.find('.dropzone').on('dragover', _.bind(this.dragover, this));
      this.$el.find('.dropzone').on('drop', _.bind(this.drop, this));
      this.$el.find('[name=file]').on('change', _.bind(this.fileSelected, this));
    },

    dragover: function(e) {
      e.stopPropagation();
      e.preventDefault();
      e.originalEvent.dataTransfer.dropEffect = 'copy';

      this.$el.find('.alert').hide();
    },

    drop: function(e) {
      e.stopPropagation();
      e.preventDefault();

      this.importFile(e.originalEvent.dataTransfer.files[0]);
    },

    fileSelected: function(e) {
      this.$el.find('.alert').hide();
      this.importFile(e.originalEvent.target.files[0]);
    },

    importFile: function(file) {
      // Import this file as a new document. The server processes
      // the file and then sends back a JSON description of the full
      // document, which we then use to create a new document
      // and redirect to that document page.
      //
      // We use the FormData interface which is supported in all decent
      // browsers and IE 10+.
      //
      // https://developer.mozilla.org/en-US/docs/Web/Guide/Using_FormData_Objects

      var self = this;
      var formData = new FormData();

      this.$el.find('.file-inputs').hide();
      this.$el.find('.progress').show();

      formData.append('file', file);
      formData.append('outputformat', 'json');

      // convert to JSON
      $.ajax({
        url: '/api/convert',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,

      }).then(function(data) {
        // we've got a JSON description back, create the new document
        $.post('/api/documents', data)
          .then(function(data) {
            window.location = '/documents/' + data.id;
          }).fail(function(xhr, status, message) {
            console.log(message);
            self.$el.find('.progress').hide();
            self.$el.find('.file-inputs').show();

            if (xhr.status == 400) {
              self.$el.find('.alert').show().text("We couldn't import the file: " + xhr.responseJSON[0]);
            }
          });

      }).fail(function(xhr, status, message) {
        console.log(message);
        self.$el.find('.progress').hide();
        self.$el.find('.file-inputs').show();

        if (xhr.status == 400) {
          var error = xhr.responseJSON.file || xhr.responseJSON[0];
          self.$el.find('.alert').show().text("We couldn't import the file: " + error);
        }
      });
    },

  });
})(window);
