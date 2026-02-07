export default class TaskBulkUpdate {
  constructor (element) {
    this.element = element;
    this.form = this.element.querySelector('#bulk-task-update-form');
    this.selectedTasks = [];

    if (!this.form) {
      return;
    }

    this.element.addEventListener('change', (event) => {
      if (event.target.matches('input[type=checkbox][name=tasks]')) {
        this.taskSelected(event);
      }
    });
  }

  taskSelected (event) {
    const selected = Array.from(this.element.querySelectorAll('input[type=checkbox][name=tasks]:checked'));
    this.selectedTasks = selected.map((input) => input.value);

    const card = event.target.closest('.card-body');
    if (card) {
      card.classList.toggle('bg-selected', event.target.checked);
    }

    this.updateFormOptions();
  }

  updateFormOptions () {
    if (!this.form) {
      return;
    }

    if (this.selectedTasks.length > 0) {
      for (const sibling of Array.from(this.form.parentElement.children)) {
        if (sibling !== this.form) {
          sibling.classList.add('d-none');
        }
      }
      this.form.classList.remove('d-none');
    } else {
      for (const sibling of Array.from(this.form.parentElement.children)) {
        if (sibling !== this.form) {
          sibling.classList.remove('d-none');
        }
      }
      this.form.classList.add('d-none');
    }

    const formData = new URLSearchParams(new FormData(this.form));
    formData.append('unassign', '');

    fetch(this.form.dataset.assigneesUrl, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'X-CSRFToken': window.Indigo.csrfToken
      },
      body: formData
    })
      .then(async (response) => {
        if (response.ok) {
          const menu = this.form.querySelector('.dropdown-menu');
          if (!menu) {
            return;
          }
          menu.innerHTML = await response.text();
        }
      })
      .catch(() => {
        // ignore failures
      });
  }
}
