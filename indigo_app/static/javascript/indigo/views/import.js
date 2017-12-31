(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.ImportView = Backbone.View.extend({
    el: '#import-document',
    events: {
      'click .btn.choose-file': 'chooseFile',
      'click .btn.import': 'submitForm',
      'dragleave .dropzone': 'noDrag',
      'dragover .dropzone': 'dragover',
      'drop .dropzone': 'drop',
      'change [name=file]': 'fileSelected',
    },

    initialize: function() {
      this.$form = this.$el.find('form.import-form');
    },

    dragover: function(e) {
      e.stopPropagation();
      e.preventDefault();
      e.originalEvent.dataTransfer.dropEffect = 'copy';
      this.$('.dropzone').addClass('incoming');
      this.$('.alert').hide();
    },

    noDrag: function() {
      this.$('.dropzone').removeClass('incoming');
    },

    drop: function(e) {
      e.stopPropagation();
      e.preventDefault();
      this.$('.dropzone').removeClass('dragging incoming');

      this.setFile(e.originalEvent.dataTransfer.files[0]);
    },

    chooseFile: function(e) {
      this.$('[name=file]').click();
    },

    fileSelected: function(e) {
      this.$('.alert').hide();
      this.setFile(e.originalEvent.target.files[0]);
    },

    setFile: function(file) {
      var self = this;

      this.file = file;
      this.$('.file-detail').text(this.file.name);
      this.$('button.import').prop('disabled', false);

      if (this.file.type == "application/pdf") {

        var reader = new FileReader();
        reader.onload = function() {
          self.drawPDF(this.result);
        };
        reader.readAsArrayBuffer(this.file);

      } else {
        this.$('.pages').hide();
      }
    },

    drawPDF: function(data) {
      var self = this,
          container = this.$('.pages').empty().show()[0],
          pageHeight = 550,
          nextLeft = 100;

      function renderPage(pdf, pageNum) {
        pdf.getPage(pageNum).then(function(page) {
          var canvas = document.createElement('canvas');
          canvas.setAttribute('id', 'page-' + pageNum);
          canvas.setAttribute('class', 'page');
          container.appendChild(canvas);

          var scale = pageHeight / page.getViewport(1).height;
          var viewport = page.getViewport(scale);
          canvas.height = viewport.height;
          canvas.width = viewport.width;
          canvas.style.left = nextLeft + 'px';

          nextLeft = nextLeft + canvas.width + 5 + 2;

          page.render({
            canvasContext: canvas.getContext('2d'),
            viewport: viewport
          }).then(function() {
            if (pageNum < pdf.numPages) {
              renderPage(pdf, pageNum + 1);
            } else {
              var padding = document.createElement('div');
              padding.setAttribute('class', 'padding');
              padding.style.left = nextLeft + 'px';
              container.append(padding);
            }
          });
        });
      }

      PDFJS.getDocument({data: data}).then(function(pdf) {
        renderPage(pdf, 1);
      });
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
                      this.$('[name="file_options.section_number_position"]:checked').val());
      formData.append('country', this.$('[name=country]').val());

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
