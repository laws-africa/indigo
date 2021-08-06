<template>
  <li :class="`toc-item${expanded ? '--active' : ''}`" v-show="showItem">
    <div class="toc-item__action">
      <div class="toc-item__action__left">
        <button class="toggle-button"
                v-if="isParent"
                @click="toggleExpandedState"
        >
          <span v-html="expanded ? collapseIconHtml : expandIconHtml"></span>
        </button>
        <button @click="onTitleClick" class="toc__title">
          {{title}}
        </button>
      </div>
      <div class="toc-item__action__right" v-if="rightIcon">
        <component :is="rightIcon" />
      </div>
    </div>
    <ol v-if="isParent" v-show="expanded" class="toc-item__children" ref="children-container">
      <TOCItem
          v-for="(item, index) in children"
          :key="index"
          :title = "item.title"
          :onTitleClick="item.onTitleClick"
          :children="item.children"
          :right-icon="rightIcon"
          :ref="`child_item_${index}`"
          :items-render-from-filter="itemsRenderFromFilter"
      />
    </ol>
  </li>
</template>

<script>
export default {
  name: 'TOCItem',
  data: () => ({
    expanded: false,
  }),
  props: {
    collapseIconHtml: {
      type: String,
      default: '-',
    },
    expandIconHtml: {
      type: String,
      default: '+',
    },
    title: {
      type: String,
      default: ""
    },
    children: {
      type: Array,
      default: () => [],
    },
    onTitleClick: {
      type: Function,
      default: () => false,
    },
    rightIcon: {
      type: Object,
      default: null,
    },
    itemsRenderFromFilter:  {
      type: Array,
      default: () => []
    }
  },

  computed: {
    isParent () {
      return this.children && this.children.length;
    },
    showItem () {
      if(!this.itemsRenderFromFilter.length) {
        return true;
      }
      console.log(this.itemsRenderFromFilter.some(item => item.title === this.title))
      return this.itemsRenderFromFilter.length && this.itemsRenderFromFilter.some(item => item.title === this.title)
    }
  },

  methods: {
    toggleExpandedState() {
      if (this.isParent) this.expanded = !this.expanded;
    },
    expandItemAndDescendants() {
      this.expanded = true;
      if(this.children.length) {
        this.children.forEach((_, index) => {
          this.$refs[`child_item_${index}`][0].expandItemAndDescendants();
        })
      }
    },

    collapseItemAndDescendants() {
      this.expanded = false;
      if(this.children.length) {
        this.children.forEach((_, index) => {
          this.$refs[`child_item_${index}`][0].collapseItemAndDescendants();
        })
      }
    },
  },
}
</script>

<style scoped>
.toc-item__action {
  display: flex;
  flex-flow: row nowrap;
  justify-content: space-between;
}

.toc-item__action__left {
  display: flex;
  flex-flow: row nowrap;
}

.toc-item__action__right {
  text-align: right;
}
</style>
