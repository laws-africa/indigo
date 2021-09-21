<template>
  <t-o-c-controller
      :items="tocItems"
      ref="tocController"
      @on-title-click="onTitleClick"
  >
    <template v-slot:search="{ model, clearTitleQuery }">
      <div class="input-group mb-2">
        <input type="text"
               class="form-control form-control-sm"
               placeholder="Search by title"
               v-model="model.titleQuery"
        >
        <div class="input-group-prepend">
          <button class="btn btn-sm btn-secondary"
                  type="button"
                  @click="clearTitleQuery"
                  :disabled="!model.titleQuery"
          >
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
    </template>
    <template v-slot:expand-collapse-toggle="{ expandAll, collapseAll }">
      <div class="d-flex mb-2">
        <button @click="expandAll" class="btn btn-primary btn-sm mr-1">Expand All</button>
        <button @click="collapseAll" class="btn btn-primary btn-sm">Collapse All</button>
      </div>
    </template>
  </t-o-c-controller>
</template>

<script>
import TOCController from "./toc-controller/index.vue";

export default {
  name: 'DocumentTOCView',
  components: {
    TOCController
  },
  props: {
    backBoneContext: {
      type: Object,
      required: true,
    }
  },
  data () {
    return {
      toc: [],
      roots: [],
      issues: null,
      tocItems: [],
    }
  },

  methods: {
    rebuild (force) {
      // recalculate the TOC from the model
      if (this.backBoneContext.model.xmlDocument) {
        console.log('rebuilding TOC');
        const oldLength = this.toc.length,
            index = this.backBoneContext.selection.get('index');

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

    buildToc () {
      // Get the table of contents of this document
      // roots is a list of the root elements of the toc tree
      // toc is an ordered list of all items in the toc
      const roots = [],
          toc = [];
      const tradition = Indigo.traditions.get(this.backBoneContext.model.document.get('country'));

      const iterateChildren = (node, parentItem) => {
        const kids = node.children;

        for (let i = 0; i < kids.length; i++) {
          let kid = kids[i],
              tocItem = null;

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
      }

      const getHeadingText = (node) => {
        let headingText = '';
        const result = this.backBoneContext.model.xpath('./a:heading//text()[not(ancestor::a:authorialNote)]', node);

        for (let i = 0; i < result.snapshotLength; i++) {
          headingText += result.snapshotItem(i).textContent;
        }

        return headingText;
      }

      function generateToc (node) {
        const $node = $(node);
        const $component = $node.closest('attachment');
        let qualified_id = node.getAttribute('eId');

        if ($component.length > 0) {
          qualified_id = $component.attr('eId') + '/' + qualified_id;
        }

        const item = {
          'num': $node.children('num').text(),
          'heading': getHeadingText(node),
          'element': node,
          'type': node.localName,
          'id': qualified_id,
        };
        item.title = tradition.toc_element_title(item);
        return item;
      }

      iterateChildren(this.backBoneContext.model.xmlDocument);

      this.toc = toc;
      this.roots = roots;

      this.mergeIssues();
    },

    issuesChanged () {
      this.mergeIssues();
      this.render();
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
        severity = _.contains(severity, 'error') ? 'error' : (_.contains(severity, 'warning') ? 'warning': 'information');

        entry.issues_title = entry.issues.length + ' issue' + (entry.issues.length === 1 ? '' : 's');
        entry.issues_description = entry.issues.map((issue) => { return issue.get('message'); }).join('<br>');
        entry.issues_severity = severity;
      });
    },

    entryForElement (element) {
      // find the TOC entry for an XML element
      const tradition = Indigo.traditions.get(this.backBoneContext.model.document.get('country')),
          toc = this.toc;

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

    render () {
      const formatItems = (item) => {
        const rightIcon = (() => {
          if(item.issues && item.issues.length) {
            const icon = document.createElement('i');
            icon.className = 'float-right issue-icon issue-' + item.issues_severity;
            icon.dataset.toggle = 'popover';
            icon.dataset.content = item.issues_description;
            icon.dataset.title = item.issues_title;
            icon.dataset.trigger = 'hover';
            icon.dataset.placement = 'bottom';
            icon.dataset.html = true;
            return icon.outerHTML;
          }
          return null;
        })();
        return ({
          title: item.title,
          children: item.children && item.children.length ? item.children.map(formatItems) : [],
          rightIcon,
          index: item.index,
          selected: item.selected,
        });
      }

      this.tocItems = this.roots.map(formatItems);
      $('#toc [data-toggle="popover"]').popover();
      this.$refs.tocController.expandAll();
    },

    // select the i-th item in the TOC
    selectItem (i, force) {
      const index = this.backBoneContext.selection.get('index');

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
          this.backBoneContext.selection.clear({silent: true});
        }
        this.backBoneContext.selection.set(i > -1 ? this.toc[i] : {});
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

    onTitleClick(index) {
      if (!Indigo.view.bodyEditorView || Indigo.view.bodyEditorView.canCancelEdits()) {
        this.selectItem(index, true);
      }
    }
  },

  watch: {
    issues () { this.issuesChanged() }
  },

  mounted() {
    this.backBoneContext.model.on('change:dom', this.rebuild, this.backBoneContext);
    this.issues = this.backBoneContext.issues;
  }
}
</script>
