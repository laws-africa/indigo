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
      this.selection = new Backbone.Model({
        index: -1,
      });
      this.toc = [];
      this.model.on('change', this.rebuild, this);
      this.template = Handlebars.compile($(this.template).html());
    },

    rebuild: function() {
      // recalculate the TOC from the model
      if (this.model.xmlDocument) {
        console.log('rebuilding TOC');

        var oldLength = this.toc.length,
            index = this.selection.get('index');
        this.toc = this.buildToc();

        if (index > this.toc.length-1) {
          // we've selected past the end of the TOC
          this.selectItem(this.toc.length-1);

        } else if (index > -1 && this.toc.length != oldLength) {
          // arrangament of the TOC has changed, re-select the item we want
          this.selectItem(index, true);

        } else {
          if (index > -1) {
            this.toc[index].selected = true;
          }

          this.render();
        }
      }
    },

    buildToc: function() {
      // Get the table of contents of this document
      var toc = [];
      var tradition = Indigo.traditions.get(this.model.document.get('country'));

      function iter_children(node, parent_item) {
        var kids = node.children;

        for (var i = 0; i < kids.length; i++) {
          var kid = kids[i],
              toc_item = null;

          if (tradition.is_toc_element(kid)) {
            toc_item = generate_toc(kid);
            toc_item.index = toc.length;
            toc.push(toc_item);

            if (parent_item) parent_item.has_children = true;
          }

          iter_children(kid, toc_item || parent_item);
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
        item.title = tradition.toc_element_title(item);
        return item;
      }

      iter_children(this.model.xmlDocument);

      return toc;
    },

    render: function() {
      this.$el.html(this.template({toc: this.toc}));
      this.$el.find('[title]').tooltip();
    },

    // select the i-th item in the TOC
    selectItem: function(i, force) {
      var index = this.selection.get('index');

      i = Math.min(this.toc.length-1, i);

      if (force || index != i) {
        // unmark the old one
        if (index > -1 && index < this.toc.length) {
          delete (this.toc[index].selected);
        }

        if (i > -1) {
          this.toc[i].selected = true;
        }

        this.render();

        // only do this after rendering
        this.selection.set(i > -1 ? this.toc[i] : {});
      }
    },

    click: function(e) {
      e.preventDefault();
      this.selectItem($(e.target).data('index'), true);
    },
  });
})(window);
