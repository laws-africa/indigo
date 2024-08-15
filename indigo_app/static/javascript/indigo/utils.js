$(function() {
  /* On buttons and links with a data-confirm="message" attribute,
   * show a message and stop everything if the user doesn't confirm.
   */
  function handleConfirm(e) {
    var message = this.getAttribute('data-confirm');
    if (message) {
      if (!confirm(message)) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
      }
    }
  }

  $('body').on('click', 'a[data-confirm], button[data-confirm], input[data-confirm]', handleConfirm);

  /* Handle forms submitted via ajax */
  function submitFormAjax(e) {
    var form = e.target;
    $.post(form.action, $(form).serialize());
    e.preventDefault();
  }
  $('body').on('submit', 'form[data-submit=ajax]', submitFormAjax);

  // Toasts should disappear after a few seconds
  function nukeToasts() {
    for (let el of document.querySelectorAll('.alert-dismissible.auto-dismiss')) {
      bootstrap.Alert.getOrCreateInstance(el).close();
    }
  }
  setTimeout(nukeToasts, 3 * 1000);
});
