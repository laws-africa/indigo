<template>
  <div class="toc">
    <slot name="search"
          :model="model"
          :clearTitleQuery="clearTitleQuery"
    >
    </slot>
    <slot
        name="expand-collapse-toggle"
        :expandAll="expandAll"
        :collapseAll="collapseAll"
    >
    </slot>

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
          @on-title-click="(emittedIndex) => $emit('on-title-click', emittedIndex)"
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
import debounce from 'lodash/debounce';

export default {
  name: "TOCController",
  components: {TOCItem},
  props: {
    items:  {
      type: Array,
      default: () => [],
    },
  },
  data: () => {
    return {
      model: {
        titleQuery: "",
      },
      filteredItems: [],
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
      this.model.titleQuery = ""
    },

    flattenItems(items) {
      const flattenItems = []
      const iterateFn = (item) => {
        flattenItems.push(item);
        if(item.children) item.children.forEach(iterateFn)
      }

      items.forEach(iterateFn);
      return flattenItems
    },

  },
  watch: {
    "model.titleQuery" (newTitleQuery) {
      const debounceFn = debounce(() => {
        if(newTitleQuery) {
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

          const flattenItems = this.flattenItems(filteredItems);

          this.filteredItems = [...flattenItems];
        } else {
          this.filteredItems = [];
        }
        this.expandAll();
      }, 200);
      debounceFn();
    },
  },
}
</script>
