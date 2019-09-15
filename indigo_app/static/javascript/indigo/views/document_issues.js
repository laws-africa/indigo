(function(exports) {
    "use strict";

    if (!exports.Indigo) exports.Indigo = {};
    Indigo = exports.Indigo;

    Indigo.linters = [];

    // Run linters and render document issues
    Indigo.DocumentIssuesView = Backbone.View.extend({
      el: 'body',
      template: '#issue-gutter-template',

      initialize: function(options) {
        this.document = options.document;
        this.documentContent = options.documentContent;
        this.editorView = options.editorView;
        this.model = this.document.issues = new Backbone.Collection();
        this.template = Handlebars.compile($(this.template).html());

        this.listenTo(this.editorView.sourceEditor, 'rendered', this.render);
        this.listenTo(this.model, 'change add remove', this.render);
        this.listenTo(this.documentContent, 'change', this.runLinters);
      },

      runLinters: function() {
        var issues = [];

        for (var i = 0; i < Indigo.linters.length; i++) {
          var iss = Indigo.linters[i](this.document, this.documentContent);
          if (iss && iss.length > 0) {
            issues = issues.concat(iss);
          }
        }

        this.model.reset(issues);
      },

      render: function() {
        var self = this;

        this.model.forEach(function(issue) {
          // TODO: scoped? use data attribute?
          var target = document.getElementById(issue.get('anchor').id);
          if (!target) return;

          var gutter = self.editorView.sourceEditor.ensureGutterActions(target);
          var node = $(self.template(issue.toJSON()))[0];

          gutter.append(node);
          $(node).popover({
            content: issue.get('description'),
            title: issue.get('message'),
            trigger: 'hover',
            placement: 'top',
          });
        });
      }
    });
})(window);
