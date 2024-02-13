export default class WorkForm {
  constructor (root) {
    this.root = root;

    if (this.root.querySelector('#id_work-commenced')) {
      this.root.querySelector('#id_work-commenced').addEventListener('change', (e) => {
        this.toggleCommenced(e.target.checked);
      });
    }
  }

  toggleCommenced (commenced) {
    this.root.querySelector('#commencement_details').classList.toggle('d-none', !commenced);
    // default to publication date
    const date = this.root.querySelector('#id_work-commencement_date');
    if (!date.value) {
      date.value = this.root.querySelector('#id_work-publication_date').value;
    }
  }
};
