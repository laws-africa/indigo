export default class ProgressBar {
  constructor (element) {
    this.element = element;
    this.stack = 0;
    this.pegged = false;
    // eslint-disable-next-line no-undef
    Indigo.progressView = this;
  }

  peg () {
    this.pegged = true;
    this.render();
  }

  unpeg () {
    this.pegged = false;
    this.render();
  }

  push () {
    this.stack += 1;
    this.render();
  }

  pop () {
    this.stack -= 1;
    this.render();
  }

  render () {
    // toggle "display: none" based on whether we're pegged or have any stack
    this.element.style.display = (this.pegged || this.stack > 0) ? '' : 'none';
  }
}
