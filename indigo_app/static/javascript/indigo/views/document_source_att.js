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
        this.choices = [];

        this.$view = this.$('.source-attachment-view');
        this.$dropdown = this.$('.source-attachment-list');
        this.$toggle = this.$('.source-attachment-toggle');
        this.iframe = document.getElementById('source-attachment-iframe');
        this.docx_mimetypes = {
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document': true,
          'application/msword': true,
          'application/vnd.oasis.opendocument.text': true,
          'application/rtf' : true,
          'text/rtf': true,
        };
        this.pdf_mimetypes = {
          'application/pdf': true,
          'text/html': true,
        };
        // combine docx and pdf mimetypes
        this.mime_types = Object.assign({}, this.pdf_mimetypes, this.docx_mimetypes);
        this.chosen = null;

        // work publication document
        if (this.document.work.get('publication_document')) {
          var p = this.document.work.get('publication_document');
          this.pubdoc = {
            'title': 'Publication document',
            'url': p.url,
            'id': 'pubdoc',
          };
        } else {
          this.pubdoc = null;
        }

        // amendments -- only those with publication documents
        this.amendments = _.filter(Indigo.Preloads.amendments, function(am) {
          return am.amending_work.publication_document && am.amending_work.publication_document.url;
        }).map(function(am) {
          var x = {
            'title': am.date + ' – ' + am.amending_work.frbr_uri,
            'url': am.amending_work.publication_document.url,
            'group': 'Amendments',
          };
          // something to make it unique
          x.id = x.title;
          return x;
        });
        this.amendments = _.sortBy(this.amendments, 'date').reverse();
      },

      rebuildChoices: function() {
        var self = this,
            choices;

        choices = this.attachments.filter(function(att) {
          return self.mime_types[att.get('mime_type')];
        }).map(function(att) {
          let default_choice;
          if (Object.keys(self.docx_mimetypes).includes(att.get('mime_type'))) {
            default_choice = true;
          }
          return {
            'title': att.get('filename'),
            'id': att.get('id'),
            'group': 'Attachments',
            'url': att.get('view_url'),
            default_choice,
          };
        });
        if (this.pubdoc) choices.unshift(this.pubdoc);
        if (this.amendments) choices = choices.concat(this.amendments);

        this.choices = choices;
        this.render();
      },

      render: function() {
        var dd = this.$dropdown[0],
            self = this,
            optGroup, prevGroup;

        this.$dropdown.empty();
        this.choices.forEach(function(att, i) {
          var parent = dd;

          // determine group, if any
          if (att.group) {
            if (prevGroup != att.group) {
              optGroup = document.createElement('optGroup');
              optGroup.label = att.group;
              dd.appendChild(optGroup);
            }
            parent = optGroup;
          }

          parent.appendChild(new Option(
            att.title, i.toString(), false, self.chosen && self.chosen.id === att.id
          ));
          prevGroup = att.group;
        });

        this.$toggle.attr('disabled', this.choices.length === 0);
      },

      toggle: function(e) {
        e.preventDefault();
        var show = !$(e.target).hasClass('active');

        if (show) {
          const default_choice = this.choices.find(choice => choice.default_choice) || this.choices[0];
          this.choose(this.chosen || default_choice);
        } else {
          this.$view.addClass('d-none');
          this.$('.source-attachment-toggle').removeClass('active');
        }
      },

      choose: function(item) {
        if (this.chosen !== item) {
          this.chosen = item;
          if (this.chosen) {
            this.iframe.src = this.chosen.url;
            this.$('.source-attachment-pop').attr('href', this.chosen.url);
          }
        }

        this.$view.removeClass('d-none');
        this.$('.source-attachment-toggle').addClass('active');
        this.render();
      },

      itemChanged: function(e) {
        this.choose(this.choices[parseInt(e.target.value)]);
      },
    });
})(window);
