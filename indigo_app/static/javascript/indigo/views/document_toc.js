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
      this.on('deselect', function() { this.selectItem(-1); });
    },

    rebuild: function() {
      // recalculate the TOC from the model
      if (this.model.xmlDocument) {
        console.log('rebuilding TOC');

        var oldLength = this.toc.length;
        this.toc = this.buildToc();

        if (this.selectedIndex > this.toc.length-1) {
          // we've selected past the end of the TOC
          this.selectItem(this.toc.length-1);

        } else if (this.selectedIndex > -1 && this.toc.length != oldLength) {
          // arrangament of the TOC has changed, re-select the item we want
          this.selectItem(this.selectedIndex, true);

        } else {
          if (this.selectedIndex > -1) {
            this.toc[this.selectedIndex].selected = true;
          }

          this.render();
        }
      }
    },

    buildToc: function() {
      // Get the table of contents of this document
      var toc = [];

      // these are the nodes we're interested in
      var interesting = {
        coverpage: 1,
        preface: 1,
        preamble: 1,
        part: 1,
        chapter: 1,
        section: 1,
        conclusions: 1,
        components: 1,
        component: 1,
        akomaNtoso: 1,
      };

      var titles = {
        akomaNtoso: function(i) { return "Entire document"; },
        coverpage: function(i) { return "Coverpage"; },
        preface: function(i) { return "Preface"; },
        preamble: function(i) { return "Preamble"; },
        conclusions: function(i) { return "Conclusions"; },
        chapter: function(i) { return "Ch. " + i.num + " " + i.heading; },
        part: function(i) { return "Part " + i.num + " " + i.heading; },
        components: function(i) { return 'Schedules'; },
        component: function(i) { 
          var alias = i.element.querySelector('FRBRalias');
          if (alias) {
            return alias.getAttribute('value');
          }

          var component = i.element.querySelector('FRBRWork FRBRthis');
          if (component) {
            var parts = component.getAttribute('value').split('/');
            component = parts[parts.length-1];
          } else {
            component = i.element.getAttribute('name') || "Component";
          }

          var match = component.match(/([^0-9]+)([0-9]+)/);
          if (match) {
            component = match[1] + ' ' + match[2];
          }

          return component.charAt(0).toUpperCase() + component.slice(1);
        },
        null: function(i) { return i.num + " " + i.heading; },
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
        item.title = (titles[item.type] || titles[null])(item);
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
      i = Math.min(this.toc.length-1, i);

      if (force || this.selectedIndex != i) {
        // unmark the old one
        if (this.selectedIndex > -1 && this.selectedIndex < this.toc.length) {
          delete (this.toc[this.selectedIndex].selected);
        }

        if (i > -1) {
          this.toc[i].selected = true;
        }

        this.selectedIndex = i;
        this.render();

        // only do this after rendering
        this.trigger('item-selected', i > -1 ? this.toc[i] : null);
      }
    },

    click: function(e) {
      e.preventDefault();
      this.selectItem($(e.target).data('index'), true);
    },
  });
})(window);
