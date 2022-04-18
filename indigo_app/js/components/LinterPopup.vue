<template>
  <div>
    <div v-if="issue">
      <h6>{{ issue.message }}</h6>
      {{ issue.description }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'LinterPopup',
  props: ['issue']
};
</script>
