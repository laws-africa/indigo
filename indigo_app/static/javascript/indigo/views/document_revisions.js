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
    },

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());
      this.document = options.document;

      this.model = new Indigo.RevisionList(null, {document: this.document});
      this.model.on('change sync', this.render, this);
      this.model.fetch({reset: true});
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
        var revision = this.model.get($(e.target).data('id'));
        this.restoreToRevision(revision);
      }
    },

    showRevision: function(e) {
      e.preventDefault();
      var $revision = $(e.currentTarget);

      $revision.siblings().removeClass('active');
      $revision.addClass('active');
    },

    restoreToRevision: function(revision) {
      $.post(revision.url() + '/restore')
        .then(function() {
          window.location.reload();
        });
    },
  });
})(window);
