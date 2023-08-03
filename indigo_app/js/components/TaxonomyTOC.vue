<template>
    <la-table-of-contents-controller
        :items.prop="taxonomy_toc"
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
    return {
      taxonomy_toc: JSON.parse(document.querySelector('#taxonomy_toc').textContent),
    };
  },
  mounted () {
    const params = new URLSearchParams(window.location.search);
    const toc = document.getElementsByTagName('la-table-of-contents-controller');
    toc[0].addEventListener('itemRendered', (e) => {
      const tocItem = e.target;
      if (!tocItem) return;
      const anchor = tocItem.querySelector('.content__action__title');
      const href = new URLSearchParams(anchor.getAttribute('href'));
      if (params.get('taxonomy_topic') === href.get('taxonomy_topic')) {
        anchor.classList.add('active');
      }
    });
  }
};
</script>
