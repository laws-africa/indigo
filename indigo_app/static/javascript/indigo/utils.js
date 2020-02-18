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

  $('body').on('click', 'a[data-confirm], button[data-confirm]', handleConfirm);

  /* Handle forms submitted via ajax */
  function submitFormAjax(e) {
    var form = e.target;
    $.post(form.action, $(form).serialize());
    e.preventDefault();
  }
  $('body').on('submit', 'form[data-submit=ajax]', submitFormAjax);

  // Toasts should disappear after a few seconds
  function nukeToasts() {
    $('.alert-dismissible.auto-dismiss').alert('close');
  }
  setTimeout(nukeToasts, 3 * 1000);
});

/* Show popover when hovering on selected links.
 * Links should have a 'data-popup-url' attribute.
 */
var _popupCache = {};

$('body').on('mouseenter', 'a[data-popup-url]', function() {
  var _this = this;
  var url = $(this).data('popup-url');
  var notFound = '<i>(not found)</i>';

  $.ajaxSetup({
    url: "work_popup.html",
    global: false,
  });

  function popup(html) {
    $(_this).popover({content: html, html: true}).popover('show');
  }

  if (_popupCache[url]) {
    popup(_popupCache[url]);
  } else {
    $.get(url).then(function(html) {
      _popupCache[url] = html;
      popup(html);
    }).fail(function(resp) {
      _popupCache[url] = notFound;
      popup(notFound);
    });
  }

  $('.popover').mouseleave(function () {
    $(_this).popover('hide');
  });
}).on('mouseleave','a[data-popup-url], .popover', function(){
  var _this = this;
  setTimeout(function () {
    if (!$('.popover:hover').length) {
      $(_this).popover('hide');
    }
  }, 300);
});
