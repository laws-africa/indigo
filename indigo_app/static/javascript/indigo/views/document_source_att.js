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
        this.mime_types = {'application/pdf': true, 'text/html': true};
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
          return {
            'title': am.date + ' - ' + am.amending_work.frbr_uri,
            'url': am.amending_work.publication_document.url,
            'group': 'Amendments',
          };
        });
        this.amendments = _.sortBy(this.amendments, 'date');
      },

      rebuildChoices: function() {
        var self = this,
            choices;

        choices = this.attachments.filter(function(att) {
          return self.mime_types[att.get('mime_type')];
        }).map(function(att) {
          return {
            'title': att.get('filename'),
            'url': att.get('view_url'),
            'id': att.get('id'),
            'group': 'Attachments',
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
          this.choose(this.chosen || this.choices[0]);
        } else {
          this.$view.addClass('d-none');
          this.$('.source-attachment-toggle').removeClass('active');
        }
      },

      choose: function(item) {
        if (this.chosen !== item) {
          this.chosen = item;
          this.iframe.src = this.chosen.url,
          this.$('.source-attachment-pop').attr('href', this.chosen.url);
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
