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
      this.selectedIndex = -1;
      this.model.on('change', this.rebuild, this);
      this.template = Handlebars.compile($(this.template).html());
    },

    rebuild: function() {
      // recalculate the TOC from the model
      if (this.model.xmlDocument) {
        console.log('rebuilding TOC');

        this.toc = this.buildToc(this.model.xmlDocument);

        if (this.selectedIndex > toc.length-1) {
          // this triggers a re-render
          this.selectItem(toc.length-1);
        } else {
          if (this.selectedIndex > -1) {
            this.toc[this.selectedIndex].selected = true;
          }
          this.render();
        }
      }
    },

    buildToc: function(root) {
      // Get the table of contents of this document
      var toc = [];
      var interesting = {
        coverpage: 1,
        preface: 1,
        preamble: 1,
        part: 1,
        chapter: 1,
        section: 1,
        conclusions: 1,
      };

      function iter_children(node) {
        var kids = node.children;

        for (var i = 0; i < kids.length; i++) {
          var kid = kids[i];
          var name = kid.localName;

          if (interesting[name]) {
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

    // select the i-th item in the TOC
    selectItem: function(i) {
      i = Math.min(this.toc.length-1, i);

      if (this.selectedIndex != i) {
        // unmark the old one
        if (this.selectedIndex > -1 && this.selectedIndex < this.toc.length) {
          delete (this.toc[this.selectedIndex].selected);
        }

        this.selectedIndex = i;
        this.toc[i].selected = true;
        this.render();

        this.trigger('item-selected', this.toc[i].element);
      }
    },

    click: function(e) {
      e.preventDefault();
      this.selectItem($(e.target).data('index'));
    },
  });
})(window);
