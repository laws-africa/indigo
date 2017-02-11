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
      var msg = xhr.statusText;
      if (xhr.responseJSON && xhr.responseJSON.detail) {
        msg = xhr.responseJSON.detail;
      }

      // 500-level status code?
      if (Math.trunc(xhr.status/100) == 5) {
        Indigo.errorView.show("Whoops, something went wrong. " + xhr.statusText);

      } else if (xhr.status == 405) {
        // method not allowed
        Indigo.errorView.show(msg);

      } else if (xhr.status == 403) {
        // permission denied
        if (Indigo.userView.model.authenticated()) {
          Indigo.errorView.show("You aren't allowed to do that.");
        } else {
          Indigo.errorView.show("Please log in first.");
        }
      }
    })
    .ajaxStart(function(event) {
      Indigo.progressView.push();
    })
    .ajaxStop(function(event) {
      Indigo.progressView.pop();
    });

  // error tracking with GA
  window.addEventListener('error', function(e) {
    if (typeof ga === 'function') {
      ga('send', 'exception', {
        'exDescription': e.message + ' @ ' + e.filename + ': ' + e.lineno,
        'exFatal': true,
      });
    }
  });

  // datepicker
  $.fn.datepicker.defaults.format = "yyyy-mm-dd";
  $.fn.datepicker.defaults.autoclose = true;

  // tooltips
  $('[title]').tooltip({
    container: 'body',
    placement: 'auto top'
  });

  Indigo.progressView = new Indigo.ProgressView();
  Indigo.errorView = new Indigo.ErrorBoxView();

  // helpers
  Indigo.toXml = function(node) {
    return new XMLSerializer().serializeToString(node);
  };
  Indigo.ga = function() {
    // google analytics are only in production
    if (window.ga) {
      ga.apply(null, arguments);
    }
  };

  // setup the library
  Indigo.library = new Indigo.Library();
  if (Indigo.Preloads.library) {
    Indigo.library.reset({results: Indigo.Preloads.library}, {parse: true});
  }

  // always load the user view
  Indigo.userView = new Indigo.UserView();

  // what view must we load?
  var view = $('body').data('backbone-view');
  if (view && Indigo[view]) {
    Indigo.view = new Indigo[view]();
    Indigo.view.render();
  }
});
