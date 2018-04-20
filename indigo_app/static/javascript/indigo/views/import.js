(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Manages the movement/selection of the crop box for PDF file import.
   */
  Indigo.CropBoxView = Backbone.View.extend({
    cornerSize: 15,
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
      this.listenTo(this.cropbox, 'change', this.refresh);
    },

    createBox: function(svg) {
      var g = svg.group().addClass('cropbox'),
          s = this.cornerSize;

      g.rect(0, 0).addClass('box').attr('data-movement', 'move');
      // add box corners
      ['ne', 'nw', 'se', 'sw'].forEach(function(c) {
        g.rect(s, s).addClass(c).addClass('corner').attr('data-movement', c);
      });
    },

    newPages: function(width, height) {
      this.$boxes = this.$('.cropbox');

      this.pageWidth = width;
      this.pageHeight = height;
      this.cropbox.set({
        left: 20,
        top: 20,
        width: this.pageWidth - 20 * 2,
        height: this.pageHeight - 20 * 2,
      }).trigger('change');
    },

    /* Calculate the final cropbox, return an array [left, top, width, height]
     * in PDF coordinates.
     */
    calculateCropBox: function(scale) {
      var attrs = this.cropbox.attributes;

      return [
        attrs.left / scale,
        attrs.top / scale,
        attrs.width / scale,
        attrs.height / scale,
      ];
    },

    mousemove: function(e) {
      if (this.moving) {
        var dx = e.originalEvent.movementX,
            dy = e.originalEvent.movementY,
            attrs = this.cropbox.attributes;

        this.cropbox.set({
          left:   Math.min(this.pageWidth,  Math.max(0, attrs.left + this.movement[0] * dx)),
          top:    Math.min(this.pageHeight, Math.max(0, attrs.top + this.movement[1] * dy)),
          width:  Math.min(this.pageWidth,  Math.max(0, attrs.width + this.movement[2] * dx)),
          height: Math.min(this.pageHeight, Math.max(0, attrs.height + this.movement[3] * dy)),
        });
      }
    },

    mousedown: function(e) {
      this.moving = true;

      // how this movement will affect the cropbox:
      //   left (x), top (y), width (x), height (y)
      this.movement = {
        'nw':   [1, 1, -1, -1],
        'ne':   [0, 1,  1, -1],
        'sw':   [1, 0, -1,  1],
        'se':   [0, 0,  1,  1],
        'move': [1, 1,  0,  0],
      }[e.target.getAttribute('data-movement')];
    },

    mouseup: function(e) {
      this.moving = false;
    },

    refresh: function() {
      var w = this.cropbox.get('width'),
          h = this.cropbox.get('height');

      this.$boxes.attr('transform', 'translate(' + this.cropbox.get('left') + ',' + this.cropbox.get('top') + ')');
      this.$boxes.find('.box').attr({
        width: w,
        height: h,
      });
      this.$boxes.find('.ne').attr('x', w - this.cornerSize);
      this.$boxes.find('.se').attr({
        x: w - this.cornerSize,
        y: h - this.cornerSize,
      });
      this.$boxes.find('.sw').attr('y', h - this.cornerSize);
    },
  });

  Indigo.ImportView = Backbone.View.extend({
    el: '#import-document',
    events: {
      'click .btn.choose-file': 'chooseFile',
      'click .btn.choose-work': 'chooseWork',
      'click .btn.import': 'submitForm',
      'dragleave .dropzone': 'noDrag',
      'dragover .dropzone': 'dragover',
      'drop .dropzone': 'drop',
      'change [name=file]': 'fileSelected',
    },
    workTemplate: '#work-detail-template',

    initialize: function() {
      this.$form = this.$el.find('form.import-form');
      this.cropBoxView = new Indigo.CropBoxView();
      this.workTemplate = Handlebars.compile($(this.workTemplate).html());

      // are we starting with an injected frbr_uri for a work?
      if (Indigo.Preloads.work) {
        var work = new Indigo.Work(Indigo.Preloads.work);
        this.setWork(work);
      }

      // are we starting with an injected expression date?
      this.expression_date = Indigo.queryParams.expression_date;
    },

    chooseWork: function() {
      var chooser = new Indigo.WorkChooserView({}),
          self = this;

      chooser.setFilters({country: Indigo.userView.model.get('country_code').toLowerCase()});
      chooser.showModal().done(function(chosen) {
        if (chosen) {
          self.setWork(chosen);
        }
      });
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
      this.$('button.import').prop('disabled', !(!!this.work));

      if (this.file.type == "application/pdf") {
        var reader = new FileReader();
        reader.onload = function() {
          self.drawPDF(this.result);
        };
        reader.readAsArrayBuffer(this.file);
      } else {
        this.scale = null;
        this.$('.pages').hide();
      }
    },

    setWork: function(work) {
      this.work = work;
      this.$('button.import').prop('disabled', !(!!this.work && !!this.file));
      this.$('#work-info').empty().html(this.workTemplate(this.work.toJSON()));
    },

    /**
     * Renders the full pdf onto a set of pages, so that we can draw cropbox
     * controls around them. The PDFs are rendered onto a canvas element
     * and then turned into an image to be used in an SVG object. This makes
     * it easier to update the cropbox overly than working on canvas directly.
     */
    drawPDF: function(data) {
      var self = this,
          container = this.$('.pages').empty().show().addClass('loading')[0],
          pageHeight = 550,
          nextLeft = 100;

      function renderPage(pdf, pageNum) {
        var page = document.createElement('page');
        page.setAttribute('class', 'page loading');
        page.id = 'pdf-page-' + pageNum;
        page.style.width = '338px';
        page.style.height = '550px';
        page.style.left = nextLeft + 'px';
        container.appendChild(page);

        pdf.getPage(pageNum).then(function(pdfPage) {
          var canvas = document.createElement('canvas');

          self.scale = pageHeight / pdfPage.getViewport(1).height;
          var viewport = pdfPage.getViewport(self.scale);
          canvas.height = viewport.height;
          canvas.width = viewport.width;

          pdfPage.render({
            canvasContext: canvas.getContext('2d'),
            viewport: viewport
          }).then(function() {
            page.style.width = canvas.width + 'px';
            page.style.height = canvas.height + 'px';
            page.classList.remove('loading');
            nextLeft = nextLeft + canvas.width + 5 + 2; // spacing and border

            var svg = SVG(page).size(canvas.width, canvas.height);
            svg.image(canvas.toDataURL(), canvas.width, canvas.height);
            self.cropBoxView.createBox(svg);

            if (pageNum < pdf.numPages) {
              // next page
              renderPage(pdf, pageNum + 1);
            } else {
              // we're done
              // last padding element
              var padding = document.createElement('div');
              padding.setAttribute('class', 'padding');
              padding.style.left = nextLeft + 'px';
              container.append(padding);
              container.classList.remove('loading');

              self.cropBoxView.newPages(canvas.width, canvas.height);
            }
          });
        });
      }

      // kick off the rendering, one page at a time
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

      formData.append('country', this.work.get('country'));
      formData.append('frbr_uri', this.work.get('frbr_uri'));
      formData.append('file', this.file);
      formData.append('file_options..section_number_position',
                      this.$('[name="file_options.section_number_position"]:checked').val());
      if (this.expression_date) {
        formData.append('expression_date', this.expression_date);
      }
      // cropbox info?
      if (this.scale) formData.append('file_options..cropbox', this.cropBoxView.calculateCropBox(this.scale));

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
