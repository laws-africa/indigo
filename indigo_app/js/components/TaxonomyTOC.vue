<template>
    <la-table-of-contents-controller
        :items.prop="taxonomy"
        collapse-all-btn-classes="btn btn-sm btn-secondary"
        expand-all-btn-classes="btn btn-sm btn-secondary"
        title-filter-clear-btn-classes="btn btn-sm btn-secondary"
        title-filter-input-classes="form-field"
        title-filter-placeholder="Filter by topic"
        class="taxonomy-sidebar"
    ></la-table-of-contents-controller>
</template>

<script>
export default {
  name: 'TaxonomyTOC',
  data () {
    const taxonomy = JSON.parse(document.querySelector('#taxonomy_toc').textContent);
    const current = new URLSearchParams(window.location.search).get('taxonomy_topic');

    // Set expanded state of current item and its parents
    function formatItem (x) {
      const children = (x.children || []).map(y => formatItem(y));
      x.expanded = x.data.slug === current || children.some(y => y.expanded);
      return x;
    }
    taxonomy.map(x => formatItem(x));

    return {
      taxonomy,
      current
    };
  },
  mounted () {
    const toc = document.getElementsByTagName('la-table-of-contents-controller');
    toc[0].addEventListener('itemRendered', (e) => {
      const tocItem = e.target;
      if (!tocItem) return;
      if (this.current === tocItem.item.data?.slug) {
        tocItem.querySelector('.content__action__title').classList.add('active');
      }
    });
  }
};
</script>
