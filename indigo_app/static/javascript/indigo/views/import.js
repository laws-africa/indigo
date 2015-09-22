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

      this.$el.find('.dropzone')
        .on('dragenter', function() { $(this).addClass('dragging'); })
        .on('dragleave', function() { $(this).removeClass('dragging'); })
        .on('dragover', _.bind(this.dragover, this))
        .on('drop', _.bind(this.drop, this));
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
      this.$el.find('.dropzone').removeClass('dragging');

      this.importFile(e.originalEvent.dataTransfer.files[0]);
    },

    fileSelected: function(e) {
      this.$el.find('.alert').hide();
      this.importFile(e.originalEvent.target.files[0]);
    },

    importFile: function(file) {
      // We use the FormData interface which is supported in all decent
      // browsers and IE 10+.
      //
      // https://developer.mozilla.org/en-US/docs/Web/Guide/Using_FormData_Objects

      var self = this;
      var formData = new FormData();

      this.$el.find('.file-inputs').hide();
      this.$el.find('.progress-box').show();

      formData.append('file', file);

      // convert to JSON
      $.ajax({
        url: '/api/documents',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,

      }).then(function(data) {
        // success, go edit it
        Indigo.progressView.peg();
        window.location = '/documents/' + data.id;

      }).fail(function(xhr, status, message) {
        var error = message || status;

        console.log(message);
        self.$el.find('.progress-box').hide();
        self.$el.find('.file-inputs').show();

        if (xhr.responseJSON) {
          error = xhr.responseJSON.file || xhr.responseJSON[0] || message;
        }

        self.$el.find('.alert').show().text("We couldn't import the file: " + error);
      });
    },

  });
})(window);
