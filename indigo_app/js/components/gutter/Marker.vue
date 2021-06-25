<template>
  <div ref="main" :style="styles" :class="classes" class="gutter-marker" @click="activate"></div>
</template>

<script>
export default {
  name: 'GutterMarker',
  props: ['marker'],
  mounted () {
    this.$refs.main.appendChild(this.marker.contentElement);
  },
  methods: {
    activate () {
      this.$emit('activate', this.marker);
    }
  },
  computed: {
    styles () {
      return `top: ${this.marker.top}px`;
    },
    classes () {
      return {
        'marker-active': this.marker.active
      };
    }
  }
};
</script>
