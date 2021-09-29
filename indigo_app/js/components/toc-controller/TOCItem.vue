<template>
  <li class="toc-item" v-show="showItem">
    <div class="toc-item__action">
      <div class="toc-item__action__left">
        <button class="toc-toggle-btn"
                v-if="isParent"
                @click="toggleExpandedState"
        >

          <span class="item-toggle-icons slot">
            <slot name="item-toggle-icons" :item="item" :expanded="expanded"></slot>
          </span>
          <!-- Shown if item-toggle-icons.slot is empty -->
          <span class="item-toggle-icons default">
            <span class="minus" v-if="expanded">-</span>
            <span class="plus" v-else>+</span>
          </span>
        </button>
        <button @click="$emit('on-title-click', index)"
                :class="`toc-item-title-btn ${selected ? 'active' : ''}`"
        >
          {{title}}
        </button>
      </div>
      <div class="toc-item__action__right">
        <slot name="right-icon" :item="item"></slot>
      </div>
    </div>
    <ol v-if="isParent" v-show="expanded" class="" ref="children-container">
      <TOCItem
          v-for="(item, index) in children"
          :title = "item.title"
          :children="item.children"
          :selected="item.selected"
          :index="item.index"
          :item="item"
          :key="index"
          :ref="`child_item_${index}`"
          :items-render-from-filter="itemsRenderFromFilter"
          @on-title-click="(emittedIndex) => $emit('on-title-click', emittedIndex)"
      >
        <template v-slot:right-icon="props">
          <slot name="right-icon" :item="props.item"></slot>
        </template>
        <template v-slot:item-toggle-icons="props">
          <slot name="item-toggle-icons" :item="props.item"></slot>
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
    item: {
      type: Object,
      default: () => ({})
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

<style scoped>

  .item-toggle-icons.default,
  .item-toggle-icons.slot:empty {
    visibility: hidden;
  }
  .item-toggle-icons.slot:empty + .item-toggle-icons.default {
    visibility: visible;
  }

</style>
