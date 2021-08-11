<template>
  <li class="toc-item" v-show="showItem">
    <div class="toc-item__action">
      <div class="toc-item__action__left">
        <button class="toc-toggle-btn"
                v-if="isParent"
                @click="toggleExpandedState"
        >
          <i class="fas fa-minus" v-if="expanded"></i>
          <i class="fas fa-plus" v-else></i>
        </button>
        <button @click="$emit('on-title-click', index)"
                :class="`toc-item-title-btn ${selected ? 'active' : ''}`"
        >
          {{title}}
        </button>
      </div>
      <div class="toc-item__action__right">
        <slot name="right-icon"></slot>
      </div>
    </div>
    <ol v-if="isParent" v-show="expanded" class="" ref="children-container">
      <TOCItem
          v-for="(item, index) in children"
          :key="index"
          :title = "item.title"
          :children="item.children"
          :ref="`child_item_${index}`"
          :index="item.index"
          :items-render-from-filter="itemsRenderFromFilter"
          :selected="item.selected"
          @on-title-click="(emittedIndex) => $emit('on-title-click', emittedIndex)"
      >
        <template v-slot:right-icon v-if="item.rightIcon">
          <span v-html="item.rightIcon"></span>
        </template>
      </TOCItem>
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

    selected: {
      type: Boolean,
      default: false,
    },

    itemsRenderFromFilter:  {
      type: Array,
      default: () => []
    },
    index: {
      type: Number,
      default: 0,
    },
  },

  computed: {
    isParent () {
      return this.children && this.children.length;
    },
    showItem () {
      // Show everything because search field is empty
      if(!this.itemsRenderFromFilter.length) {
        return true;
      }
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
