<template>
  <div>
    <div v-if="issue">
      <h6>{{ issue.message }}</h6>
      <div>{{ issue.description }}</div>
      <button
        v-if="issue.fixCaption"
        class="btn btn-sm btn-outline-primary mt-2"
        type="button"
        @click="fix"
      >{{ issue.fixCaption }}</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LinterPopup',
  props: ['issue'],
  methods: {
    fix () {
      this.$emit('fix', this.issue);
    }
  }
};
</script>
