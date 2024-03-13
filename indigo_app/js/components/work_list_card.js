export default class WorkListCard {
  constructor (element) {
    this.element = element;
    this.element.addEventListener('click', (e) => this.clicked(e));
    this.detail = document.querySelector(this.element.getAttribute('hx-target'));
    if (this.detail) {
      this.collapse = new window.bootstrap.Collapse(this.detail, { toggle: false });
      this.detail.addEventListener('hide.bs.collapse', () => this.element.classList.add('collapsed'));
      this.detail.addEventListener('show.bs.collapse', () => this.element.classList.remove('collapsed'));
    }
  }

  clicked (event) {
    if (!this.collapse) return;
    if (event.target.tagName === 'A') return;
    this.collapse.toggle();
  }
}
