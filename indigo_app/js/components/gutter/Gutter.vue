<template>
  <aside class="gutter">
    <div ref="gutterItems" class="gutter-items">
      <GutterMarker
        v-for="m in markers"
        :key="m.id"
        :marker="m"
        @activate="activate" />
    </div>
  </aside>
</template>

<script>
import { GutterLayout } from './layout';
import GutterMarker from './Marker.vue';
import debounce from 'lodash/debounce';

/**
 * This Gutter component makes it possible to show markers / indicators / interactive elements
 * in a gutter alongside a main content element. Each gutter item is positioned horizontally
 * so that it aligns with an anchor element inside the main content. When the anchor element
 * moves, so will the gutter item.
 *
 * A single element can be marked as active, which will give it priority when being positioned.
 */
export default {
  name: 'Gutter',
  components: { GutterMarker },
  data: () => ({
    items: [],
    activeItem: null,
    contentRoot: null,
    markers: []
  }),
  mounted () {
    this._ids = 0;
    if (this.contentRoot) this.setupLayout();
  },
  watch: {
    contentRoot () {
      this.setupLayout();
    },
    items () {
      this.markers = this.items.map((item) => {
        return {
          // Vue wants unique ids
          id: this._ids++,
          item: item,
          active: this.activeItem === item,
          top: 1,
          // these are used by the gutter layout algorithm
          anchorElement: item.anchorElement,
          contentElement: item.contentElement
        };
      });
    },
    activeItem () {
      for (const m of this.markers) {
        m.active = m.item === this.activeItem;
      }
      // Only run the layout on the next tick, to give the gutter items an opportunity to respond
      // to the change in active item (eg. after event bubbling). They may update their content and change
      // their dimensions, which impacts layout.
      this.$nextTick(() => this.runLayout());
    },
    markers () {
      this.runLayout();
    }
  },
  methods: {
    activate (marker) {
      this.activeItem = marker.item;
    },
    runLayout () {
      if (this.layout) {
        const activeMarker = this.markers.find(m => m.item === this.activeItem);
        this.layout.layout(this.markers, activeMarker);
      }
    },
    setupLayout () {
      this.layout = new GutterLayout(this.contentRoot);

      if (window.ResizeObserver) {
        if (this.observer) this.observer.disconnect();

        const delay = 250;
        // add observer to re-layout when the containing document changes size, which implies marker positions will change
        this.observer = new ResizeObserver(debounce(this.runLayout.bind(this), delay));
        this.observer.observe(this.contentRoot);
      }
    }
  }
};
</script>
