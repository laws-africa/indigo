(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Manages the movement/selection of the crop box for PDF file import.
   */
  Indigo.CropBoxView = Backbone.View.extend({
    el: '.pages',
    events: {
      'mousemove': 'mousemove',
      'mousedown .cropbox': 'mousedown',
    },

    initialize: function() {
      // handle mouseup even when outside of the pages element
      document.body.addEventListener('mouseup', _.bind(this.mouseup, this));

      this.moving = false;
      this.cropbox = new Backbone.Model({
        top: 0,
        left: 0,
        width: 0,
        height: 0,
      });
      this.listenTo(this.cropbox, 'change', this.render);
    },

    newPages: function(width, height) {
      this.$boxes = this.$('.cropbox');

      this.pageWidth = width;
      this.pageHeight = height;
      this.cropbox.set({
        top: 20,
        left: 20,
        width: this.pageWidth - 20 * 2,
        height: this.pageHeight - 20 * 2,
      });
    },

    mousemove: function(e) {
      if (!this.moving) return;

      this.cropbox.set({
        top:  Math.min(this.pageWidth, Math.max(0, this.cropbox.get('top') + e.originalEvent.movementX)),
        left: Math.min(this.pageHeight, Math.max(0, this.cropbox.get('left') + e.originalEvent.movementY)),
      });
    },

    mousedown: function(e) {
      this.moving = true;
    },

    mouseup: function(e) {
      this.moving = false;
    },

    render: function() {
      this.$boxes.attr('x', this.cropbox.get('top'));
      this.$boxes.attr('y', this.cropbox.get('left'));
      this.$boxes.attr('width', this.cropbox.get('width'));
      this.$boxes.attr('height', this.cropbox.get('height'));
    },
  });

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
      this.cropBoxView = new Indigo.CropBoxView();
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

          var scale = pageHeight / page.getViewport(1).height;
          var viewport = page.getViewport(scale);
          canvas.height = viewport.height;
          canvas.width = viewport.width;

          page.render({
            canvasContext: canvas.getContext('2d'),
            viewport: viewport
          }).then(function() {
            var page = document.createElement('div');
            page.setAttribute('class', 'page');
            page.style.width = canvas.width + 2 + 'px';
            page.style.height = canvas.height + 2 + 'px';
            page.style.left = nextLeft + 'px';
            page.id = 'page-' + pageNum;
            nextLeft = nextLeft + canvas.width + 5 + 2;
            container.appendChild(page);

            renderPageWithCrop(page, canvas);

            if (pageNum < pdf.numPages) {
              // next page
              renderPage(pdf, pageNum + 1);
            } else {
              // last padding element
              var padding = document.createElement('div');
              padding.setAttribute('class', 'padding');
              padding.style.left = nextLeft + 'px';
              container.append(padding);

              self.cropBoxView.newPages(canvas.width, canvas.height);
            }
          });
        });
      }

      function renderPageWithCrop(page, canvas) {
        var svg = SVG(page).size(canvas.width, canvas.height);

        svg.image(canvas.toDataURL(), canvas.width, canvas.height);
        svg.rect(0, 0).addClass('cropbox');
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
