(function(exports) {
    "use strict";

    if (!exports.Indigo) exports.Indigo = {};
    Indigo = exports.Indigo;

    // Run linters and render document issues
    Indigo.DocumentIssuesView = Backbone.View.extend({
      el: 'body',
      template: '#issue-gutter-template',

      initialize: function(options) {
        this.document = options.document;
        this.attachments = this.document.attachments();
        this.documentContent = options.documentContent;
        this.editorView = options.editorView;
        this.model = this.document.issues;
        this.template = Handlebars.compile($(this.template).html());
        this.$akn = this.$('#document-sheet la-akoma-ntoso');
        this.nodes = [];

        this.listenTo(this.editorView.sourceEditor, 'rendered', this.render);
        this.listenTo(this.model, 'reset change add remove', this.render);
        this.listenTo(this.documentContent, 'change', this.runLinters);
        this.listenTo(this.attachments, 'reset change add remove', this.runLinters);
      },

      getLinters: function(document) {
        var linters = [];

        document.tradition().settings.linters.forEach(function(name) {
          var fn = Indigo.Linting.linters[name];
          if (fn) {
            linters.push(fn);
          }
        });

        return linters;
      },

      runLinters: function() {
        var issues = [],
            linters = this.getLinters(this.document),
            self = this;

        linters.forEach(function(linter) {
          var iss = linter(self.document, self.documentContent);
          if (iss && iss.length > 0) {
            issues = issues.concat(iss);
          }
        });

        this.model.reset(issues);
      },

      render: function() {
        var self = this,
            displayed = {};

        // remove existing nodes
        for (const node of this.nodes) {
          node.remove();
        }
        this.nodes = [];

        this.model.forEach(function(issue) {
          // Only attach a particular issue to a node once. This is required for linters that, for example, identify
          // elements with duplicate ids and produce an issue for each copy of the ID. Since we display them based
          // on ID, we want to avoid display the same issue multiple times for each element with that ID.

          var anchor_id = issue.get('anchor').id,
              ident = anchor_id + '/' + issue.get('code'),
              targets;

          if (displayed[ident]) return;
          displayed[ident] = true;

          // this assumes that the issue id is scoped (ie. to a schedule, etc.)
          targets = self.$akn.find('[id="' + anchor_id + '"]');

          for (var i = 0; i < targets.length; i++) {
            var target = targets[i];

            var gutter = self.editorView.sourceEditor.ensureGutterActions(target);
            var node = $(self.template(issue.toJSON()))[0];
            self.nodes.push(node);

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
