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

export class AmendmentInstructionApplyForm {
  constructor (form) {
    this.form = form;
    this.button = this.form.querySelector('.btn-success');
    if (this.button) {
      this.button.addEventListener('click', (e) => this.click(e));
    }
  }

  async click () {
    this.button.setAttribute('disabled', true);
    try {
      await window.Indigo.view.save();
      this.form.requestSubmit();
    } catch {
      // only re-enable the button if there was an error. on success, the whole element is re-loaded
      this.button.removeAttribute('disabled');
    }
  }
}
