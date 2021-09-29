<template>
  <li class="toc-item" v-show="showItem">
    <div class="toc-item__indent">
      <button class="toc-toggle-btn"
              v-if="isParent"
              @click="toggleExpandedState"
      >
        <slot name="collapse-icon" v-if="expanded">
          <span class="minus">-</span>
        </slot>
        <slot name="expand-icon" v-else>
          <span class="plus">+</span>
        </slot>
      </button>
    </div>
    <div class="toc-item__content">
      <div :class="`toc-item__content__action ${item.selected ? 'active' : ''}`">
        <button @click="$emit('on-title-click', item.index)"
                class="toc-item__content__action__btn"
        >
          {{item.title}}
        </button>
        <div class="right-icon">
          <slot name="right-icon" :item="item"></slot>
        </div>
      </div>
      <ol v-if="isParent" v-show="expanded" class="" ref="children-container">
        <TOCItem
            v-for="(childItem, index) in item.children"
            :item="childItem"
            :key="index"
            :ref="`child_item_${index}`"
            :items-render-from-filter="itemsRenderFromFilter"
            @on-title-click="(emittedIndex) => $emit('on-title-click', emittedIndex)"
        >
          <template v-slot:right-icon="props">
            <slot name="right-icon" :item="props.item"></slot>
          </template>
          <template v-slot:expand-icon><slot name="expand-icon"></slot></template>
          <template v-slot:collapse-icon><slot name="collapse-icon"></slot></template>
        </TOCItem>
      </ol>
    </div>
  </li>
</template>

<script>
export default {
  name: 'TOCItem',
  data: () => ({
    expanded: false,
  }),
  props: {
    item: {
      type: Object,
      default: () => ({}),
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
      return this.item.children && this.item.children.length;
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
      if(this.item.children && this.item.children.length) {
        this.item.children.forEach((_, index) => {
          this.$refs[`child_item_${index}`][0].expandItemAndDescendants();
        })
      }
    },

    collapseItemAndDescendants() {
      this.expanded = false;
      if(this.item.children && this.item.children.length) {
        this.item.children.forEach((_, index) => {
          this.$refs[`child_item_${index}`][0].collapseItemAndDescendants();
        })
      }
    },
  },
}
</script>

<style scoped>
.toc-item {
  display: flex;
  align-items: flex-start;
  width: 100%;
}

.toc-item ol {
  list-style: none;
  padding: 0px;
  margin: 0 !important;
}


.toc-item__indent {
  width: 19px;
  padding-top: 2px;
}

.toc-item__content {
  width: 100%;
}

.toc-item__content__action {
  display: flex;
  justify-content: space-between;
  width: 100%;
  transition: background-color 300ms ease-in-out, border-color 300ms ease-in-out;
  padding: 2px;
  border: 2px solid transparent;
  border-radius: 3px;

}

.toc-item__content__action__btn {
  background-color: transparent;
  border: none;
  flex: 1;
  text-align: left;
  outline: none;
  color: #2d7ad4;
}

.toc-item__content__action:hover {
  background-color: #e9ecef;
}

.toc-item__content__action.active {
  border-color: #2d7ad4;
}



</style>
