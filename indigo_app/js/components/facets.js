export class FacetGroup {
  constructor (root) {
    this.root = root;

    // handle negation on facet items
    this.root.addEventListener('click', (event) => {
      if (event.target.classList.contains('negate')) {
        event.preventDefault();
        this.negate(event.target.parentElement);
      }
    });
  }

  negate (group) {
    const input = group.querySelector('input');
    if (input) {
      // toggle the value of the input
      if (input.value.startsWith('-')) {
        input.value = input.value.slice(1);
      } else {
        input.value = '-' + input.value;
      }
      input.checked = true;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }
}

export class RemoveFacetButton {
  constructor (root) {
    this.root = root;
    this.root.addEventListener('click', (e) => this.removeFacet(e));
  }

  removeFacet () {
    const form = document.getElementById(this.root.dataset.form);
    const name = this.root.dataset.name;

    if (name && form) {
      for (const input of form[name]) {
        if (input.value === this.root.dataset.value) {
          input.checked = false;
          input.dispatchEvent(new Event('change', { bubbles: true }));
        }
      }
    }
  }
}
