<template>
  <div class="toc-controller-wrapper">
    <div class="input-group mb-2">
      <input type="text"
             class="form-control form-control-sm"
             placeholder="Search by title"
             v-model="titleQuery"
      >
      <div class="input-group-prepend">
        <button class="btn btn-sm btn-secondary"
                style="width: 25px"
                type="button"
                @click="clearTitleQuery"
                :disabled="!titleQuery"
        >
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>
    <div class="d-flex mb-2">
      <button @click="expandAllTOCItems"
              type="button"
              class="btn btn-primary btn-sm mr-1"
      >
        Expand All
      </button>
      <button @click="collapseAllTOCItems"
              type="button"
              class="btn btn-primary btn-sm">
        Collapse All
      </button>
    </div>
    <TOCController
        :items="roots"
        :title-query="titleQuery"
        ref="tocController"
        @on-title-click="onTitleClick"
    >
      <template v-slot:right-icon="{item}">
        <i :class="`float-right issue-icon issue-${item.issues_severity}`"
           v-if="item.issues.length"
           data-toggle="popover"
           :data-content="item.issues_description"
           :data-title="item.issues_title"
           data-trigger="hover"
           data-placement="bottom"
           data-html="true"
           data-container=".toc-controller-wrapper"
        >
        </i>
      </template>

      <template v-slot:expand-icon><i class="fas fa-plus"></i></template>
      <template v-slot:collapse-icon><i class="fas fa-minus"></i></template>
    </TOCController>
  </div>
</template>

<script>
import TOCController from './toc-controller/index.vue';

export default {
  name: 'DocumentTOCView',
  components: {
    TOCController
  },
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
    rebuild (force) {
      // recalculate the TOC from the model
      if (this.model.xmlDocument) {
        console.log('rebuilding TOC');
        const oldLength = this.toc.length;
        const index = this.selection.get('index');

        this.buildToc();

        if (index > this.toc.length - 1) {
          // we've selected past the end of the TOC
          this.selectItem(this.toc.length - 1);
        } else if (force || (index > -1 && this.toc.length !== oldLength)) {
          // arrangament of the TOC has changed, re-select the item we want
          this.selectItem(index, true);
        } else {
          if (index > -1) {
            this.toc[index].selected = true;
          }
        }
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
        const $node = $(node);
        const $component = $node.closest('attachment');
        let qualified_id = node.getAttribute('eId');

        if ($component.length > 0) {
          qualified_id = $component.attr('eId') + '/' + qualified_id;
        }

        const item = {
          num: $node.children('num').text(),
          heading: getHeadingText(node),
          element: node,
          type: node.localName,
          id: qualified_id,
          selected: false,
          issues: [],
          issues_title: '',
          issues_description: '',
          issues_severity: ''
        };
        item.title = tradition.toc_element_title(item);
        return item;
      }

      iterateChildren(this.model.xmlDocument);

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
    selectItem (i, force) {
      const index = this.selection.get('index');

      i = Math.min(this.toc.length - 1, i);

      if (force || index !== i) {
        // unmark the old one
        if (index > -1 && index < this.toc.length) {
          this.toc[index].selected = false;
        }

        if (i > -1) {
          this.toc[i].selected = true;
        }

        // only do this after rendering
        if (force) {
          // ensure it forces a change
          this.selection.clear({ silent: true });
        }
        this.selection.set(i > -1 ? this.toc[i] : {});
      }
    },

    selectItemById (itemId) {
      for (let i = 0; i < this.toc.length; i++) {
        if (this.toc[i].id === itemId) {
          this.selectItem(i, true);
          return true;
        }
      }

      return false;
    },

    onTitleClick (index) {
      if (!Indigo.view.bodyEditorView || Indigo.view.bodyEditorView.canCancelEdits()) {
        this.selectItem(index, true);
      }
    },

    clearTitleQuery () { this.titleQuery = ''; },

    expandAllTOCItems () { this.$refs.tocController.expandAll(); },
    collapseAllTOCItems () { this.$refs.tocController.collapseAll(); }
  },

  watch: {
    issues () { this.mergeIssues(); }
  },

  updated () {
    $('#toc [data-toggle="popover"]').popover();
  },

  mounted () {
    this.model.on('change:dom', this.rebuild, this);
  }
};
</script>

<style>
  .toc-controller-wrapper .popover {
    max-width: 200px !important;
  }
</style>
