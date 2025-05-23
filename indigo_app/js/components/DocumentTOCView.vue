<template>
  <div class="toc-controller-wrapper">
    <la-table-of-contents-controller
        ref="la-toc-controller"
        :items.prop="roots"
        :title-filter="titleQuery"
        expand-all-btn-classes="btn btn-primary btn-sm me-1"
        collapse-all-btn-classes="btn btn-primary btn-sm mr-1"
        title-filter-input-classes="form-control form-control-sm"
        title-filter-clear-btn-classes="btn btn-sm btn-secondary"
        v-on:itemRendered="handleItemRendered"
        v-on:itemTitleClicked="onTitleClick"
    >
      <span slot="expand-icon"><i class="fas fa-plus"></i></span>
      <span slot="collapse-icon"><i class="fas fa-minus"></i></span>
    </la-table-of-contents-controller>
  </div>
</template>

<script>
export default {
  name: 'DocumentTOCView',
  props: {
    selection: {
      type: Object,
      required: true
    },
    model: {
      type: Object,
      required: true
    },
    issues: {
      type: Object,
      required: true
    }
  },
  data () {
    return {
      titleQuery: '',
      toc: [],
      roots: [],
      tocItems: []
    };
  },

  methods: {
    handleItemRendered (e) {
      if (e.target.item.issues.length) {
        const icon = document.createElement('i');
        icon.className = `float-right issue-icon issue-${e.target.item.issues_severity}`;
        icon.dataset.toggle = 'popover';
        icon.dataset.content = e.target.item.issues_description;
        icon.dataset.title = e.target.item.issues_title;
        icon.dataset.trigger = 'hover';
        icon.dataset.placement = 'bottom';
        icon.dataset.html = true;
        icon.dataset.container = '.toc-controller-wrapper';
        e.target.appendHtml = icon.outerHTML;
        $('#toc [data-toggle="popover"]').popover();
      }
    },
    rebuild () {
      // recalculate the TOC from the model
      if (this.model.xmlDocument) {
        console.log('rebuilding TOC');
        this.buildToc();
        this.selectItem(this.selection.get('index'));
      }
    },

    buildToc () {
      // Get the table of contents of this document
      // roots is a list of the root elements of the toc tree
      // toc is an ordered list of all items in the toc
      const roots = [];
      const toc = [];
      const tradition = Indigo.traditions.get(this.model.document.get('country'));

      const iterateChildren = (node, parentItem) => {
        const kids = node.children;

        for (let i = 0; i < kids.length; i++) {
          const kid = kids[i];
          let tocItem = null;

          if (tradition.is_toc_deadend(kid)) continue;

          if (tradition.is_toc_element(kid)) {
            tocItem = generateToc(kid);
            tocItem.index = toc.length;
            toc.push(tocItem);

            if (parentItem) {
              parentItem.children = parentItem.children || [];
              parentItem.children.push(tocItem);
            } else {
              roots.push(tocItem);
            }
          }

          iterateChildren(kid, tocItem || parentItem);
        }
      };

      const getHeadingText = (node) => {
        let headingText = '';
        const result = this.model.xpath('./a:heading//text()[not(ancestor::a:authorialNote)]', node);

        for (let i = 0; i < result.snapshotLength; i++) {
          headingText += result.snapshotItem(i).textContent;
        }

        return headingText;
      };

      function generateToc (node) {
        let num = null;
        for (const n of node.children) {
          if (n.localName === 'num') {
            num = n;
            break;
          }
        }

        const item = {
          num: num ? num.textContent : '',
          heading: getHeadingText(node),
          element: node,
          type: node.localName,
          id: node.getAttribute('eId'),
          issues: [],
          issues_title: '',
          issues_description: '',
          issues_severity: ''
        };
        item.title = tradition.toc_element_title(item);
        return item;
      }

      iterateChildren(this.model.xmlDocument);

      // move the top-level akomaNtoso element from being the first parent, to just the first sibling of its children
      // this makes more sense in the TOC view and takes up less horizontal space
      if (toc.length > 0 && toc[0].type === 'akomaNtoso' && toc[0].children) {
        roots.push(...toc[0].children);
        toc[0].children = [];
      }

      this.toc = toc;
      this.roots = roots;

      this.mergeIssues();
    },

    mergeIssues () {
      // fold document issues into the TOC
      const withIssues = [];

      _.each(this.toc, (entry) => {
        entry.issues = [];
      });

      this.issues.each((issue) => {
        // find the toc entry for this issue
        const element = issue.get('element');

        if (element) {
          const entry = this.entryForElement(element);
          if (entry) {
            entry.issues.push(issue);
            withIssues.push(entry);
          }
        }
      });

      // now attach decent issue descriptions
      _.each(withIssues, (entry) => {
        let severity = _.map(entry.issues, (issue) => { return issue.get('severity'); });
        severity = _.contains(severity, 'error') ? 'error' : (_.contains(severity, 'warning') ? 'warning' : 'information');

        entry.issues_title = entry.issues.length + ' issue' + (entry.issues.length === 1 ? '' : 's');
        entry.issues_description = entry.issues.map((issue) => { return issue.get('message'); }).join('<br>');
        entry.issues_severity = severity;
      });
    },

    entryForElement (element) {
      // find the TOC entry for an XML element
      const tradition = Indigo.traditions.get(this.model.document.get('country'));
      const toc = this.toc;

      // first, find the closest element's ancestor that is a toc element
      while (element) {
        if (tradition.is_toc_element(element)) {
          // now get the toc item for this element
          for (let i = 0; i < toc.length; i++) {
            if (toc[i].element === element) return toc[i];
          }
        }

        element = element.parentElement;
      }
    },

    // select the i-th item in the TOC
    selectItem (i) {
      i = Math.min(this.toc.length - 1, i);

      const tocItems = this.$refs['la-toc-controller'].querySelectorAll('la-toc-item');
      for (const tocItem of tocItems) {
        tocItem.classList.remove('selected');
        if (tocItem.item.index === i) {
          tocItem.classList.add('selected');
        }
      }

      // clear first to ensure a change event
      this.selection.clear({ silent: true });
      this.selection.set(i > -1 ? this.toc[i] : {});
    },

    selectItemById (itemId) {
      for (let i = 0; i < this.toc.length; i++) {
        if (this.toc[i].id === itemId) {
          this.selectItem(i);
          return true;
        }
      }

      return false;
    },

    onTitleClick (e) {
      e.detail.preventDefault();
      if (!Indigo.view.sourceEditorView || Indigo.view.sourceEditorView.confirmAndDiscardChanges()) {
        this.selectItem(e.target.item.index);
      }
    }
  },

  watch: {
    issues () { this.mergeIssues(); }
  },

  mounted () {
    this.model.on('change:dom', this.rebuild, this);
  }
};
</script>

<style>
  .toc-controller-wrapper {
    padding-bottom: 50px;
  }
  .toc-controller-wrapper .popover {
    max-width: 200px !important;
  }
</style>
