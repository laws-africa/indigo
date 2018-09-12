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
        if (Indigo.user.authenticated()) {
          Indigo.errorView.show("You aren't allowed to do that.");
        } else {
          Indigo.errorView.show("Please log in first.");
        }
      } else if (xhr.status == 400) {
        var details;
        msg = "There was a problem with your request";

        if (xhr.responseJSON && _.isObject(xhr.responseJSON)) {
          details = "<ul>";
          details += _.map(xhr.responseJSON, function(val, key) {
            return '<li>' + key.replace('_', ' ') + ": " + val + "</li>";
          }).join(" ");
          details += "</ul>";

          msg += ":";
        } else {
          msg += ".";
        }

        Indigo.errorView.show(msg, details);
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
    placement: 'auto',
  });

  // stash the query string params, if any
  function getQueryParams(queryString) {
    var query = (queryString || window.location.search).substring(1); // delete ?
    if (!query) {
      return {};
    }
    return _
      .chain(query.split('&'))
      .map(function(params) {
        var p = params.split('=');
        return [p[0], decodeURIComponent(p[1])];
      })
      .object()
      .value();
  }

  Indigo.queryParams = getQueryParams();

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

  // always load the user view
  Indigo.user = new Indigo.User(Indigo.Preloads.user || {
    permissions: [],
  });

  // setup the document library
  Indigo.library = new Indigo.Library();
  if (Indigo.Preloads.library) {
    Indigo.library.reset({results: Indigo.Preloads.library}, {parse: true});
  }

  // setup the collection of works
  Indigo.works = new Indigo.WorksCollection();
  Indigo.works.country = Indigo.Preloads.country_code || Indigo.user.get('country_code');
  if (Indigo.Preloads.works) {
    Indigo.works.reset({results: Indigo.Preloads.works}, {parse: true});
  }

  // what views must we load?
  var views = ($('body').data('backbone-view') || '').split(" ");
  Indigo.views = _.reject(_.map(views, function(name) {
    if (name && Indigo[name]) {
      var view = new Indigo[name]();
      Indigo.view = Indigo.view || view;
      return view;
    }
  }), function(v) { return !v; });
  _.invoke(Indigo.views, 'render');


  // osx vs windows
  var isOSX = navigator.userAgent.indexOf("OS X") > -1;
  $('body')
    .toggleClass("win", !isOSX)
    .toggleClass("osx", isOSX);

  // prevent navigating away from dirty views
  $(window).on('beforeunload', function(e) {
    if (Indigo.view && Indigo.view.isDirty && Indigo.view.isDirty()) {
      e.preventDefault();
      return 'You will lose your changes!';
    }
  });
});
