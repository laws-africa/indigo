(function(exports) {
    "use strict";

    if (!exports.Indigo) exports.Indigo = {};
    Indigo = exports.Indigo;

    // Render document issues
    Indigo.DocumentLinterView = Backbone.View.extend({
      el: 'body',
      template: '#issue-gutter-template',

      initialize: function(options) {
        this.document = options.document;
        this.editorView = options.editorView;
        this.model = this.document.issues = new Backbone.Collection();
        this.template = Handlebars.compile($(this.template).html());

        this.model.add({
            code: 'W101',
            anchor: {
              id: 'section-1',
            },
            message: 'Duplicate section number: Section 2',
            description: 'Section numbers should be unique. Is there a typo?',
            severity: 'W',
        });

        this.listenTo(this.editorView.sourceEditor, 'rendered', this.render);
        this.listenTo(this.model, 'change add remove', this.render);
      },

      render: function() {
        // TODO
        var self = this;

        this.model.forEach(function(issue) {
          // TODO: scoped? use data attribute?
          var target = document.getElementById(issue.get('anchor').id);
          if (!target) return;

          // TODO: quick-edit should be gutter - should be first child
          var gutter = target.firstElementChild && target.firstElementChild.classList.contains('quick-edit') ? target.firstElementChild : null;
          var node = $(self.template(issue.toJSON()))[0];

          if (!gutter) {
            gutter = document.createElement('div');
            gutter.className = 'quick-edit ig';
            target.prepend(gutter);
          }

          gutter.append(node);
          $(node).popover({
            content: issue.get('description'),
            title: issue.get('message'),
            trigger: 'hover',
          });
        });
      }
    });
})(window);
