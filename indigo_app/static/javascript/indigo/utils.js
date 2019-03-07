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
});

/* Show popover when hovering on selected links.
 * Links should have a 'data-popup-url' attribute.
 */
var _popupCache = {};

$('body').on('mouseenter', 'a[data-popup-url]', function() {
  var _this = this;
  var url = $(this).data('popup-url');

  function popup(html) {
    $(_this).popover({content: html, html: true}).popover('show');
  }

  if (_popupCache[url]) {
    popup(_popupCache[url]);
  } else {
    $.get(url).then(function(html) {
      _popupCache[url] = html;
      popup(html);
    });
  }

  $('.popover').mouseleave(function () {
    $(_this).popover('hide');
  });
}).on('mouseleave','a[data-popup-url]', function(){
  var _this = this;
  setTimeout(function () {
    if (!$('.popover:hover').length) {
      $(_this).popover('hide');
    }
  }, 300);
});


