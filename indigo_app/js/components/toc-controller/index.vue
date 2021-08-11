<template>
  <div data-id="toc-controller" class="toc">
    <div class="input-group mb-2">
      <input type="text"
             class="form-control form-control-sm"
             placeholder="Search by title"
             v-model="titleQuery"
      >
      <div class="input-group-prepend">
        <button class="btn btn-sm btn-secondary"
                type="button"
                @click="clearTitleQuery"
                :disabled="!titleQuery"
        >
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>

    <div class="d-flex mb-2">
      <button @click="expandAll" class="btn btn-primary btn-sm mr-1">Expand All</button>
      <button @click="collapseAll" class="btn btn-primary btn-sm">Collapse All</button>
    </div>
    <ol>
      <TOCItem
          v-for="(item, index) in items"
          :key="index"
          :title = "item.title"
          :children="item.children"
          :ref="`toc_item_${index}`"
          :itemsRenderFromFilter="filteredItems"
          :index="item.index"
          :selected="item.selected"
          @on-title-click="onTitleClick"
      >
        <template v-slot:right-icon v-if="item.rightIcon">
          <span v-html="item.rightIcon"></span>
        </template>
      </TOCItem>
    </ol>
  </div>
</template>

<script>
import TOCItem from "./TOCItem.vue";
import debounced from "../../utils/debounced";

const debounceBuilder = debounced(200);

export default {
  name: "TOCController",
  components: {TOCItem},
  props: {
    items:  {
      type: Array,
      default: () => [],
    },
    onTitleClick: {
      type: Function,
      default: () => false,
    }
  },
  data: (instance) => {
    return {
      titleQuery: "",
      filteredItems: instance.$props.items,
    }
  },
  methods: {
    expandAll() {
      this.items.forEach((_, index) => {
        if(this.$refs[`toc_item_${index}`]) this.$refs[`toc_item_${index}`][0].expandItemAndDescendants();
      });
    },
    collapseAll() {
      this.items.forEach((_, index) => {
        if(this.$refs[`toc_item_${index}`]) this.$refs[`toc_item_${index}`][0].collapseItemAndDescendants();
      });
    },
    clearTitleQuery() {
      this.titleQuery = ""
    },
  },
  watch: {
    titleQuery(newTitleQuery) {
      debounceBuilder(() => {
        /***
         * A recursive function that copies the tree, but only retaining children that have a deeper match
         * When a node matches, no deeper recursion is needed, as then the whole subtree below that node remains
         * included.
         * The map will map nodes to false when there is no match somewhere in the subtree rooted by that node.
         * These false values are then eliminated by filter(Boolean)
         * */
        const filterTree = (nodes, cb) => {
          return nodes.map(node => {
            if (cb(node)) return node;
            let children = filterTree(node.children || [], cb);
            return children.length && { ...node,  children };
          }).filter(Boolean);
        }

        const filteredItems = [...filterTree(this.items, (node) =>
            node.title.toLowerCase().includes(newTitleQuery.toLowerCase()))]

        const flattenItems = [];

        const iterateFn = (item) => {
          flattenItems.push(item);
          if(item.children) item.children.forEach(iterateFn)
        }

        filteredItems.forEach(iterateFn);
        this.filteredItems = [...flattenItems];
        this.expandAll();
      })
    },
  },
  mounted() {

  }
}
</script>
