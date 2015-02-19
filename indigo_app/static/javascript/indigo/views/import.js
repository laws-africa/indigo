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

    importFile: function(file) {
      var reader = new FileReader();

      if (file.type != 'text/xml') {
        this.$el.find('.alert').show().text('You can only upload XML files.');
        return;
      }

      var self = this;
      reader.onload = function(e) {
        var data = e.target.result;

        if (!data) {
          this.$el.find('.alert').show().text('It looks like your file was empty.');
        } else {
          self.importData(data);
        }
      };

      reader.readAsText(file);
    },

    fileSelected: function(e) {
      this.$el.find('.alert').hide();
      this.importFile(e.originalEvent.target.files[0]);
    },

    importData: function(data) {
      var self = this;

      this.$el.find('.file-inputs').hide();
      this.$el.find('.progress').show();

      $.post('/api/documents', {'frbr_uri': '/', 'content': data})
        .then(function(data) {
          window.location = '/documents/' + data.id;
        })
        .fail(function(xhr, status, message) {
          console.log(xhr);
          self.$el.find('.progress').hide();
          self.$el.find('.file-inputs').show();

          if (xhr.status == 400) {
            self.$el.find('.alert').show().text("We couldn't import the file: " + xhr.responseJSON.content);
          }
        });
    },

  });
})(window);
