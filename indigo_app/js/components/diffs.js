export class DiffNavigator {
  constructor (root) {
    this.root = root;
    this.root.querySelector('.prev-change-btn')?.addEventListener('click', () => this.prevChange());
    this.root.querySelector('.next-change-btn')?.addEventListener('click', () => this.nextChange());
    this.counterEl = this.root.querySelector('.diff-counter');
    this.refresh();
  }

  refresh () {
    this.changedElements = [];

    const target = document.querySelector(this.root.getAttribute('data-target'));
    const changedElements = target ? target.querySelectorAll('.diff-pair, ins, del, .ins, .del') : [];

    for (let i = 0; i < changedElements.length; i++) {
      const el = changedElements[i];
      // don't go inside diff-pairs, and ignore adjacent diffs
      if (!el.parentElement.classList.contains('diff-pair') && (
        this.changedElements.length === 0 || this.changedElements[this.changedElements.length - 1] !== el.previousElementSibling)) {
        this.changedElements.push(el);
      }
    }

    this.currentElementIndex = -1;
    this.updateCounter();
  }

  prevChange (e) {
    // workaround for (x - 1) % 3 == -1
    if (this.currentElementIndex <= 0) {
      this.currentElementIndex = this.changedElements.length - 1;
    } else {
      this.currentElementIndex--;
    }
    if (this.currentElementIndex > -1) this.changedElements[this.currentElementIndex].scrollIntoView();
    this.updateCounter();
  }

  nextChange (e) {
    this.currentElementIndex = (this.currentElementIndex + 1) % this.changedElements.length;
    if (this.currentElementIndex > -1) this.changedElements[this.currentElementIndex].scrollIntoView();
    this.updateCounter();
  }

  updateCounter () {
    if (this.counterEl) {
      if (this.changedElements.length === 0) {
        this.counterEl.textContent = '0';
      } else {
        this.counterEl.textContent = (this.currentElementIndex + 1) + ' / ' + this.changedElements.length;
      }
    }
  }
}
