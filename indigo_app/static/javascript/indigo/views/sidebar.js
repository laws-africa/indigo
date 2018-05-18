(function(exports) {
  "use strict";

  var $link = $('.sidebar .sidebar-minimizer');

  $link.on('click', function() {
    if (document.body.classList.toggle('sidebar-minimized')) {
      // now minimized
      $link.find('i').removeClass('fa-chevron-left').addClass('fa-chevron-right');
    } else {
      // now expanded
      $link.find('i').addClass('fa-chevron-left').removeClass('fa-chevron-right');
    }
  });
})(window);
