(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.ImportView = Backbone.View.extend({
    el: '#import-document',
    events: {
      'click .btn.choose-file': 'chooseFile',
      'click .btn.import': 'submitForm',
    },

    initialize: function() {
      var self = this;

      this.$el.find('.dropzone')
        .on('dragover', _.bind(this.dragover, this))
        .on('drop', _.bind(this.drop, this));
      this.$el.find('[name=file]').on('change', _.bind(this.fileSelected, this));
      this.$form = this.$el.find('form.import-form');
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

      this.setFile(e.originalEvent.dataTransfer.files[0]);
    },

    chooseFile: function(e) {
      this.$el.find('[name=file]').click();
    },

    fileSelected: function(e) {
      this.$el.find('.alert').hide();
      this.setFile(e.originalEvent.target.files[0]);
    },

    setFile: function(file) {
      this.file = file;
      this.$el.find('.file-detail').text(this.file.name);
      this.$el.find('button.import').prop('disabled', false);
    },

    submitForm: function(e) {
      e.preventDefault();

      // We use the FormData interface which is supported in all decent
      // browsers and IE 10+.
      //
      // https://developer.mozilla.org/en-US/docs/Web/Guide/Using_FormData_Objects

      var self = this;
      var formData = new FormData();

      formData.append('file', this.file);
      formData.append('file_options.section_number_position',
                      this.$el.find('[name="file_options.section_number_position"]:checked').val());

      this.$el.find('.file-inputs').hide();
      this.$el.find('.progress-box').show();
      this.$el.find('button.import').prop('disabled', true);

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
        self.$el.find('button.import').prop('disabled', false);

        if (xhr.responseJSON) {
          error = xhr.responseJSON.file || xhr.responseJSON[0] || message;
        }

        self.$el.find('.alert').show().text("We couldn't import the file: " + error);
      });
    },

  });
})(window);
