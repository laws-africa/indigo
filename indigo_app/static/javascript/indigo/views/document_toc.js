(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // This view shows the table-of-contents of the document and handles clicks
  Indigo.DocumentTOCView = Backbone.View.extend({
    el: '#toc',
    template: '#toc-template',
    events: {
      'click a': 'click',
    },

    initialize: function() {
      this.toc = [];
      this.model.on('change', this.modelChanged, this);
      this.template = Handlebars.compile($(this.template).html());
    },

    modelChanged: function() {
      // recalculate the TOC from the model
      if (this.model.xmlDocument) {
        this.toc = this.buildToc(this.model.xmlDocument);
        this.render();
      }
    },

    buildToc: function(root) {
      // Get the table of contents of this document
      var toc = [];

      function iter_children(node) {
        var kids = node.children;
        for (var i = 0; i < kids.length; i++) {
          var kid = kids[i];
          var name = kid.localName;

          if (name == 'part' || name == 'chapter' || name == 'section') {
            toc.push(generate_toc(kid));
          }

          iter_children(kid);
        }
      }

      function generate_toc(node) {
        var $node = $(node);
        var item = {
          'num': $node.children('num').text(),
          'heading': $node.children('heading').text(),
          'element': node,
          'type': node.localName,
          'id': node.id,
        };

        item.title = item.num + " " + item.heading;

        if (item.type == 'chapter') {
          item.title = "Ch. " + item.title;
        } else if (item.type == 'part') {
          item.title = "Part " + item.title;
        }

        return item;
      }

      iter_children(root);

      return toc;
    },

    render: function() {
      this.$el.html(this.template({toc: this.toc}));
      this.$el.find('[title]').tooltip();
    },

    click: function(e) {
      var item = this.toc[$(e.target).data('index')];
      this.trigger('item-clicked', item.element);
    },
  });
})(window);
