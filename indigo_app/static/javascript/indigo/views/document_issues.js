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
        this.$akn = this.$('#document-sheet .akoma-ntoso');

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
          // may be multiple targets with the same id
          // this assumes that the issue id is scoped (ie. to a schedule, etc.)
          var targets = self.$akn.find('[id="' + issue.get('anchor').id + '"]');

          for (var i = 0; i < targets.length; i++) {
            var target = targets[i];

            var gutter = self.editorView.sourceEditor.ensureGutterActions(target);
            var node = $(self.template(issue.toJSON()))[0];

            var content = issue.get('description');

            if (issue.get('suggestion')) {
              content = content + "<br><br><b>Tip:</b> " + issue.get('suggestion');
            }

            gutter.append(node);
            $(node).popover({
              content: content,
              title: issue.get('message'),
              trigger: 'hover',
              placement: 'bottom',
              html: true,
            });
          }
        });
      }
    });
})(window);
