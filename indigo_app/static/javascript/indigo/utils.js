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

  /**
   * Parses text into an XML document.
   * @param text
   * @returns {Document}
   * @throws {Error} if the text is not valid XML
   */
  Indigo.parseXml = function(text) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(text, "application/xml");
    if (doc.querySelector("parsererror")) {
      throw Error("Invalid XML: " + new XMLSerializer().serializeToString(doc));
    }
    return doc;
  };

  /**
   * This converts a jquery deferred into javascript promise/async function
   */
  Indigo.deferredToAsync = async function(deferred) {
    await new Promise((resolve, reject) => {
      deferred.then(resolve).fail(reject);
    });
  };
});
