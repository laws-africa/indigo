export default class ErrorBox {
  constructor (element) {
    this.element = element;
    this.message = '';
    this.html = '';
    window.Indigo.errorView = this;

    const closeButton = this.element.querySelector('.btn-close');
    if (closeButton) {
      closeButton.addEventListener('click', () => this.close());
    }
  }

  show (message, html) {
    // css makes the box 600px wide
    const left = (window.innerWidth / 2) - 300;
    this.message = message;
    this.html = html || '';
    this.render();
    this.element.style.left = `${left}px`;
    this.element.style.display = 'block';
  }

  close () {
    this.element.style.display = 'none';
  }

  render () {
    const messageEl = this.element.querySelector('.message');
    if (messageEl) {
      messageEl.textContent = this.message;
    }

    const detailEl = this.element.querySelector('.detail');
    if (detailEl) {
      detailEl.innerHTML = this.html;
    }
  }
}
