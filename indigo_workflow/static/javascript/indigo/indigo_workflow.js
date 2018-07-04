$(function() {
  function handleConfirm(e) {
    // show a message and stop everything if the user doesn't confirm
    var message = this.getAttribute('data-confirm');
    if (message) {
      if (!confirm(message)) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
      }
    }
  }

  $('body').on('click', 'a[data-confirm], button[data-confirm]', handleConfirm);
});
