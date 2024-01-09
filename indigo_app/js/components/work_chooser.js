export default class WorkChooser {
  // dismisses the modal when the main chooser form is submitted; otherwise bootstrap swallows the
  // event and htmx doesn't fire
  constructor (element) {
    element.querySelector('#work-chooser-form').addEventListener('submit', (e) => {
      $(element.parentElement).modal('hide');
    });
  }
}
