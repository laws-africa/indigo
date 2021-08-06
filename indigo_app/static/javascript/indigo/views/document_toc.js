(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // This view shows the table-of-contents of the document and handles clicks
  Indigo.DocumentTOCView = Backbone.View.extend({
    el: '#toc',
    events: {
      'click a': 'click',
    },

    initialize: function(options) {
      this.selection = new Backbone.Model({
        index: -1,
      });
      this.toc = [];
      this.roots = [];
      this.model.on('change:dom', this.rebuild, this);
      this.issues = options.document.issues;

      this.listenTo(this.issues, 'reset change add remove', this.issuesChanged);
    },

    rebuild: function(force) {
      // recalculate the TOC from the model
      if (this.model.xmlDocument) {
        console.log('rebuilding TOC');

        var oldLength = this.toc.length,
            index = this.selection.get('index');

        this.buildToc();

        if (index > this.toc.length-1) {
          // we've selected past the end of the TOC
          this.selectItem(this.toc.length-1);

        } else if (force || (index > -1 && this.toc.length !== oldLength)) {
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
      // roots is a list of the root elements of the toc tree
      // toc is an ordered list of all items in the toc
      var roots = [],
          toc = [];
      var tradition = Indigo.traditions.get(this.model.document.get('country'));
      var self = this;

      function iter_children(node, parent_item) {
        var kids = node.children;

        for (var i = 0; i < kids.length; i++) {
          var kid = kids[i],
              toc_item = null;

          if (tradition.is_toc_deadend(kid)) continue;

          if (tradition.is_toc_element(kid)) {
            toc_item = generate_toc(kid);
            toc_item.index = toc.length;
            toc.push(toc_item);

            if (parent_item) {
              parent_item.children = parent_item.children || [];
              parent_item.children.push(toc_item);
            } else {
              roots.push(toc_item);
            }
          }

          iter_children(kid, toc_item || parent_item);
        }
      }

      function getHeadingText(node) {
        var headingText = '';
        var result = self.model.xpath('./a:heading//text()[not(ancestor::a:authorialNote)]', node);

        for (var i = 0; i < result.snapshotLength; i++) {
          headingText += result.snapshotItem(i).textContent;
        }

        return headingText;
      }

      function generate_toc(node) {
        var $node = $(node);
        var $component = $node.closest('attachment');
        var qualified_id = node.getAttribute('eId');

        if ($component.length > 0) {
          qualified_id = $component.attr('eId') + '/' + qualified_id;
        }

        var item = {
          'num': $node.children('num').text(),
          'heading': getHeadingText(node),
          'element': node,
          'type': node.localName,
          'id': qualified_id,
        };
        item.title = tradition.toc_element_title(item);
        return item;
      }

      iter_children(this.model.xmlDocument);

      this.toc = toc;
      this.roots = roots;

      this.mergeIssues();
    },

    issuesChanged: function() {
      this.mergeIssues();
      this.render();
    },

    mergeIssues: function() {
      // fold document issues into the TOC
      var self = this,
          withIssues = [];

      _.each(this.toc, function(entry) {
        entry.issues = [];
      });

      this.issues.each(function(issue) {
        // find the toc entry for this issue
        var element = issue.get('element');

        if (element) {
          var entry = self.entryForElement(element);
          if (entry) {
            entry.issues.push(issue);
            withIssues.push(entry);
          }
        }
      });

      // now attach decent issue descriptions
      _.each(withIssues, function(entry) {
        var severity = _.map(entry.issues, function(issue) { return issue.get('severity'); });
        severity = _.contains(severity, 'error') ? 'error' : (_.contains(severity, 'warning') ? 'warning': 'information');

        entry.issues_title = entry.issues.length + ' issue' + (entry.issues.length === 1 ? '' : 's');
        entry.issues_description = entry.issues.map(function(issue) { return issue.get('message'); }).join('<br>');
        entry.issues_severity = severity;
      });
    },

    entryForElement: function(element) {
      // find the TOC entry for an XML element
      var tradition = Indigo.traditions.get(this.model.document.get('country')),
          toc = this.toc;

      // first, find the closest element's ancestor that is a toc element
      while (element) {
        if (tradition.is_toc_element(element)) {
          // now get the toc item for this element
          for (var i = 0; i < toc.length; i++) {
            if (toc[i].element === element) return toc[i];
          }
        }

        element = element.parentElement;
      }
    },

    render: function() {
      // recursively render the TOC
      function renderItem(root, item) {
        var li = document.createElement('li');
        li.classList.add('toc-item');

        // issues?
        if (item.issues && item.issues.length) {
          var icon = document.createElement('i');
          icon.className = 'float-right issue-icon issue-' + item.issues_severity;
          li.appendChild(icon);

          $(icon).popover({
            content: item.issues_description,
            title: item.issues_title,
            trigger: 'hover',
            placement: 'bottom',
            html: true,
          });
        }

        var a = document.createElement('a');
        a.setAttribute('href', '#');
        a.setAttribute('data-index', item.index);
        a.textContent = item.title;
        if (item.selected) a.classList.add('active');
        li.appendChild(a);

        if (item.children) {
          var kids = document.createElement('ol');
          li.appendChild(kids);
          item.children.forEach(function(x) { renderItem(kids, x); });
        }

        root.appendChild(li);
      }

      var root = document.createElement('ol');

      function formatItems (item) {
        return ({
          title: item.title,
          onTitle: function () { console.log('rusty'); },
          children: item.children && item.children.length ? item.children.map(formatItems) : [],
        });
      }

      var tocItems = this.roots.map(formatItems);
      var TOCController = window.vueData.components.TOCController;
      if(TOCController) {
        TOCController.items = [...tocItems];
        TOCController.expandAll();
      }

      this.roots.forEach(function(x) { renderItem(root, x); });
      this.$el.empty().append(root);
    },

    // select the i-th item in the TOC
    selectItem: function(i, force) {
      var index = this.selection.get('index');

      i = Math.min(this.toc.length-1, i);

      if (force || index !== i) {
        // unmark the old one
        if (index > -1 && index < this.toc.length) {
          delete (this.toc[index].selected);
        }

        if (i > -1) {
          this.toc[i].selected = true;
        }

        this.render();

        // only do this after rendering
        if (force) {
          // ensure it forces a change
          this.selection.clear({silent: true});
        }
        this.selection.set(i > -1 ? this.toc[i] : {});
      }
    },

    selectItemById: function(itemId) {
      for (var i = 0; i < this.toc.length; i++) {
        if (this.toc[i].id === itemId) {
          this.selectItem(i, true);
          return true;
        }
      }

      return false;
    },

    click: function(e) {
      e.preventDefault();
      if (!Indigo.view.bodyEditorView || Indigo.view.bodyEditorView.canCancelEdits()) {
        this.selectItem($(e.target).data('index'), true);
      }
    },
  });
})(window);
