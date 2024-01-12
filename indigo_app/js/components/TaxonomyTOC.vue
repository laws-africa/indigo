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
/**
 * This component renders the taxonomy tree as a table of contents. It has two modes:
 *
 * link: The default mode. Each item is a link to the taxonomy page.
 * checkbox: Each item is a checkbox. This is triggered when the checkbox prop is set to the field name to use.
 */
export default {
  name: 'TaxonomyTOC',
  props: ['checkbox', 'selected'],
  data () {
    const taxonomy = JSON.parse(document.querySelector('#taxonomy_toc').textContent);
    const selected = (this.selected || '').split(' ');

    // Set expanded state of current item and its parents
    function formatItem (x) {
      const children = (x.children || []).map(y => formatItem(y));
      x.expanded = selected.includes(x.data.slug) || children.some(y => y.expanded);
      return x;
    }
    taxonomy.map(x => formatItem(x));

    return {
      taxonomy,
      selectedSlugs: selected
    };
  },
  mounted () {
    const toc = document.getElementsByTagName('la-table-of-contents-controller');
    toc[0].addEventListener('itemRendered', (e) => {
      const tocItem = e.target;
      if (!tocItem) return;

      const action = tocItem.querySelector('.content__action');
      if (this.checkbox && !action.querySelector('input[type="checkbox"]')) {
        // convert link into a label
        const a = tocItem.querySelector('.content__action .content__action__title');
        const label = document.createElement('label');
        label.innerHTML = a.innerHTML;
        label.className = 'content__action__title';
        a.insertAdjacentElement('beforebegin', label);
        a.remove();

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.name = this.checkbox;
        checkbox.className = 'facet';
        checkbox.value = tocItem.item.data.slug;
        checkbox.checked = this.selectedSlugs.includes(checkbox.value);
        checkbox.setAttribute('form', 'work-filter-form');
        checkbox.addEventListener('change', (e) => this.checkboxChanged(e, tocItem));
        label.insertBefore(checkbox, label.firstChild);
      }

      if (!this.checkbox && this.selectedSlugs.includes(tocItem.item.data?.slug)) {
        action.querySelector('.content__action__title').classList.add('active');
      }

      if (tocItem.item.data.count !== undefined && !action.querySelector('.badge')) {
        const count = document.createElement('div');
        count.className = 'badge text-bg-light';
        count.innerText = (tocItem.item.data.count || '0') + (tocItem.item.children ? `/${tocItem.item.data.total}` : '');
        action.appendChild(count);
      }
    });
  },
  methods: {
    checkboxChanged (e, tocItem) {
      // toggle all children
      for (const checkbox of tocItem.querySelectorAll('input[type="checkbox"]')) {
        checkbox.checked = e.target.checked;
      }
    }
  }
};
</script>

<style>
la-toc-item input[type=checkbox] {
  margin-right: 0.25rem;
}
la-toc-item label {
  margin-bottom: 0.1rem;
}
</style>
