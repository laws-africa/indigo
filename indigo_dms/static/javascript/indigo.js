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

  // TODO: how do we know to load this view?
  Indigo.view = new Indigo.DocumentView();
});
