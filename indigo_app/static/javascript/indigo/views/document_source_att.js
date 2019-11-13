(function(exports) {
    "use strict";

    if (!exports.Indigo) exports.Indigo = {};
    Indigo = exports.Indigo;

    // Show side-by-side source attachment
    Indigo.SourceAttachmentView = Backbone.View.extend({
      el: 'body',
      events: {
        'change .source-attachment-list': 'itemChanged',
        'click .source-attachment-toggle': 'toggle',
      },

      initialize: function(options) {
        this.document = options.document;

        this.attachments = this.document.attachments();
        this.listenTo(this.attachments, 'add change remove sync', this.rebuildChoices);
        this.choices = new Indigo.AttachmentList(null, {document: this.document});
        this.listenTo(this.choices, 'change reset', this.render);

        this.$view = this.$('.source-attachment-view');
        this.$dropdown = this.$('.source-attachment-list');
        this.$toggle = this.$('.source-attachment-toggle');
        this.iframe = document.getElementById('source-attachment-iframe');
        this.mime_types = {'application/pdf': true, 'text/html': true};
        this.chosen = null;
      },

      rebuildChoices: function() {
        var self = this;
        this.choices.reset(this.attachments.filter(function(att) {
          return self.mime_types[att.get('mime_type')];
        }));
      },

      render: function() {
        var dd = this.$dropdown[0],
            self = this;

        this.$dropdown.empty();

        if (this.choices.length === 0) {
          this.$toggle.attr('disabled', true);
        } else {
          this.$toggle.attr('disabled', false);

          this.choices.each(function(att) {
            dd.appendChild(new Option(
              att.get('filename'), att.get('id'), false, self.chosen == att
            ));
          });
        }
      },

      toggle: function(e) {
        e.preventDefault();
        var show = !$(e.target).hasClass('active');

        if (show) {
          this.choose(this.chosen || this.attachments.at(0));
        } else {
          this.$view.addClass('d-none');
          this.$('.source-attachment-toggle').removeClass('active');
        }
      },

      choose: function(item) {
        item = this.attachments.get(item);

        if (this.chosen != item) {
          this.chosen = item;
          this.iframe.src = this.chosen.get('view_url');
          this.$('.source-attachment-pop').attr('href', this.chosen.get('view_url'));
        }

        this.$view.removeClass('d-none');
        this.$('.source-attachment-toggle').addClass('active');
        this.render();
      },

      itemChanged: function(e) {
        this.choose(e.target.value);
      },
    });
})(window);
