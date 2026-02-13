export default class OfflineAlert {
  constructor (element) {
    this.element = element;
    this.autoShowBound = false;
    window.Indigo.offlineNoticeView = this;
  }

  autoShow () {
    if (this.autoShowBound) {
      return;
    }

    this.autoShowBound = true;
    window.addEventListener('offline', () => this.setOffline());
    window.addEventListener('online', () => this.setOnline());
    if (!navigator.onLine) this.show();
  }

  setOnline () {
    this.hide();
  }

  setOffline () {
    this.show();
  }

  show () {
    this.element.classList.remove('d-none');
  }

  hide () {
    this.element.classList.add('d-none');
  }
}
