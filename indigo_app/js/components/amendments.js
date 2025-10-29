export class AddAmendmentButton {
  constructor (btn) {
    this.btn = btn;
    this.btn.addEventListener('click', (e) => this.click(e));
  }

  click (e) {
    e.preventDefault();

    const chooser = new window.Indigo.WorkChooserView({
      country: this.btn.getAttribute('data-country'),
      locality: this.btn.getAttribute('data-locality') || '-'
    });
    const form = document.getElementById('new-amendment-form');

    chooser.showModal().done(function (chosen) {
      if (chosen) {
        form.elements.date.value = chosen.get('commencement_date') || chosen.get('publication_date');
        form.elements.amending_work.value = chosen.get('id');
        form.submit();
      }
    });
  }
}
