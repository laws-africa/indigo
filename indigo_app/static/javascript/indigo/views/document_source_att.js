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

        // work publication documen
        if (this.document.work.get('publication_document')) {
          var p = this.document.work.get('publication_document');

          this.pubdoc = new Indigo.Attachment(this.document.work.get('publication_document'));
          this.pubdoc.set('view_url', this.pubdoc.get('url'));
          this.pubdoc.set('id', this.pubdoc.cid);
        } else {
          this.pubdoc = null;
        }
      },

      rebuildChoices: function() {
        var self = this,
            choices;

        choices = this.attachments.filter(function(att) {
          return self.mime_types[att.get('mime_type')];
        });
        if (this.pubdoc) choices.push(this.pubdoc);

        this.choices.reset(choices);
      },

      render: function() {
        var dd = this.$dropdown[0],
            self = this;

        this.$dropdown.empty();
        this.choices.each(function(att) {
          dd.appendChild(new Option(
            att.get('filename'), att.get('id'), false, self.chosen == att
          ));
        });

        this.$toggle.attr('disabled', this.choices.length == 0);
      },

      toggle: function(e) {
        e.preventDefault();
        var show = !$(e.target).hasClass('active');

        if (show) {
          this.choose(this.chosen || this.choices.at(0));
        } else {
          this.$view.addClass('d-none');
          this.$('.source-attachment-toggle').removeClass('active');
        }
      },

      choose: function(item) {
        item = this.choices.get(item);

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
