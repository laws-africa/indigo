(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handle the revisions of a document.
   */
  Indigo.DocumentRevisionsView = Backbone.View.extend({
    el: '.document-revisions-view',
    template: '#revisions-template',
    events: {
      'click .restore-revision': 'restore',
      'click .revision': 'showRevision',
      'click .dismiss': 'dismiss',
    },

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());
      this.document = options.document;
      this.documentContent = options.documentContent;

      this.model = new Indigo.RevisionList(null, {document: this.document});
      this.listenTo(this.model, 'change sync', this.render);
      this.listenTo(this.document, 'sync', this.refresh);
      this.listenTo(this.documentContent, 'sync', this.refresh);

      $('.show-revisions').on('click', _.bind(this.show, this));

      this.diffNavigator = new Indigo.DiffNavigator({el: document.querySelector('.diff-navigator')});
    },

    show: function(e) {
      e.preventDefault();
      $('.work-view').addClass('d-none');
      this.$el.removeClass('d-none');
    },

    dismiss: function(e) {
      e.preventDefault();
      $('.work-view').removeClass('d-none');
      this.$el.addClass('d-none');
    },

    refresh: function() {
      if (this.document.get('id')) {
        this.model.fetch({reset: true});
      } else {
        this.model.reset([]);
      }
    },

    render: function() {
      var revisions = this.model.toJSON();
      var week_ago = moment().subtract(7, 'days');

      _.each(revisions, function(r) {
        // format date nicely
        r.date_str = moment(r.date).calendar(null, {
          sameDay: '[Today at] LTS',
          lastDay: '[Yesterday at] LTS',
          lastWeek: '[Last] dddd [at] LTS',
          sameElse: 'LL [at] LTS',
        });
      });

      this.$el.find('.revisions-container').html(this.template({
        revisions: revisions,
      }));
    },

    restore: function(e) {
      e.preventDefault();

      if (confirm("Are you sure you want to restore back to this point?")) {
        var $revision = $(e.target).closest('.revision');
        if ($revision.data('index') == '0') {
          // last saved revision, just reload page
          Indigo.progressView.peg();
          window.location.reload();
        } else {
          this.restoreToRevision(this.model.get($revision.data('id')));
        }
      }
    },

    showRevision: function(e) {
      e.preventDefault();
      var $revision = $(e.currentTarget);
      var revision = this.model.get($revision.data('id'));
      var self = this;

      $revision.siblings().removeClass('active');
      $revision.addClass('active');

      $.get(revision.url() + '/diff')
        .then(function(response) {
          var $akn = self.$el.find('.revision-preview la-akoma-ntoso').html(response.content);
          self.$el.find('.change-count').text(
            response.n_changes + ' change' + (response.n_changes != 1 ? 's' : ''));
          self.diffNavigator.refresh();
        });
    },

    restoreToRevision: function(revision) {
      $.post(revision.url() + '/restore')
        .then(function() {
          Indigo.progressView.peg();
          // # TODO: just refresh the models!
          window.location.reload();
        });
    },
  });
})(window);
