$(function() {
  "use strict";

  Indigo.csrfToken = $('meta[name="csrf-token"]').attr('content');

  // setup CSRF
  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
      var requiresToken = !(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type));
      if (requiresToken && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", Indigo.csrfToken);
      }
    }
  });

  // global error handler
  $(document)
    .ajaxError(function(event, xhr, settings, error) {
      if (xhr.status == 500) {
        Indigo.errorView.show("Whoops, something went wrong. " + xhr.statusText);
      } else if (xhr.status == 403) {
        // permission denied
        if (Indigo.userView.model.authenticated()) {
          Indigo.errorView.show("You aren't allowed to do that. Try logging out and in again.");
        } else {
          Indigo.errorView.show("Please log in first.");
        }
      }
    })
    .ajaxStart(function(event) {
      $('#progress-bar').show();
    })
    .ajaxStop(function(event) {
      $('#progress-bar').hide();
    });

  Indigo.errorView = new Indigo.ErrorBoxView();

  // always load the user view
  Indigo.userView = new Indigo.UserView();

  // what view must we load?
  var view = $('body').data('backbone-view');
  if (view && Indigo[view]) {
    Indigo.view = new Indigo[view]();
  }
});
