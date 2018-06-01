(function(exports) {
  "use strict";

  var $link = $('.sidebar .sidebar-minimizer');

  $link.on('click', function() {
    document.body.classList.toggle('sidebar-minimized');
  });
})(window);
