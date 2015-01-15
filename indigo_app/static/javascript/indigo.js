$(function() {
  "use strict";

  // setup CSRF
  var csrfToken = $('meta[name="csrf-token"]').attr('content');
  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
      var requiresToken = !(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type));
      if (requiresToken && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", csrfToken);
      }
    }
  });

  Indigo.errorView = new Indigo.ErrorBoxView();

  // what view must we load?
  var view = $('body').data('backbone-view');
  if (view && Indigo[view]) {
    Indigo.view = new Indigo[view]();
  }
});
