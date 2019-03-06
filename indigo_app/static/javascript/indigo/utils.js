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

// Show popover when hovering on selected links
$('body').on('mouseenter', 'a[href^="/works/"]:not(.btn)', function() {
  var _this = this;
  $.get(this.href + 'popup').then(function(html) {
    $(_this).popover({content: html, html: true}).popover('show');
  });
  $('.popover').mouseleave(function () {
    $(_this).popover('hide');
  });
}).on('mouseleave','a[href^="/works/"]:not(.btn)', function(){
  var _this = this;
  setTimeout(function () {
    if (!$('.popover:hover').length) {
      $(_this).popover('hide');
    }
  }, 300);
});