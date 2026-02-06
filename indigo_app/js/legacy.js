export function legacySetup () {
  if (!window.Indigo) window.Indigo = {};
  const Indigo = window.Indigo;

  // tell monaco where to load its files from
  window.require = {
    paths: {
      vs: '/static/lib/monaco-editor'
    }
  };

  Indigo.csrfToken = $('meta[name="csrf-token"]').attr('content');

  // setup CSRF
  $.ajaxSetup({
    beforeSend: function (xhr, settings) {
      const requiresToken = !(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type));
      if (requiresToken && !this.crossDomain) {
        xhr.setRequestHeader('X-CSRFToken', Indigo.csrfToken);
      }
    }
  });

  // global error handler
  $(document)
    .ajaxError(function (event, xhr, settings, error) {
      let msg = xhr.statusText;
      if (xhr.responseJSON && xhr.responseJSON.detail) {
        msg = xhr.responseJSON.detail;
      }

      // 500-level status code?
      if (Math.trunc(xhr.status / 100) === 5) {
        Indigo.errorView.show('Whoops, something went wrong. ' + xhr.statusText);
      } else if (xhr.status === 405) {
        // method not allowed
        Indigo.errorView.show(msg);
      } else if (xhr.status === 403) {
        // permission denied
        if (Indigo.user.authenticated()) {
          Indigo.errorView.show("You aren't allowed to do that.");
        } else {
          Indigo.errorView.show('Please log in first.');
        }
      } else if (xhr.status === 400) {
        let details;
        msg = $t('There was a problem with your request');

        if (xhr.responseJSON && _.isObject(xhr.responseJSON)) {
          details = '<ul>';
          details += _.map(xhr.responseJSON, function (val, key) {
            return '<li>' + key.replace('_', ' ') + ': ' + val + '</li>';
          }).join(' ');
          details += '</ul>';

          msg += ':';
        } else {
          msg += '.';
        }

        Indigo.errorView.show(msg, details);
      }
    })
    .ajaxStart(function (event) {
      Indigo.progressView.push();
    })
    .ajaxStop(function (event) {
      Indigo.progressView.pop();
    });

  // tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"], [title]:not(.notooltip)'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // stash the query string params, if any
  function getQueryParams (queryString) {
    const query = (queryString || window.location.search).substring(1); // delete ?
    if (!query) {
      return {};
    }
    return _
      .chain(query.split('&'))
      .map(function (params) {
        const p = params.split('=');
        return [p[0], decodeURIComponent(p[1])];
      })
      .object()
      .value();
  }

  Indigo.queryParams = getQueryParams();

  Indigo.progressView = new Indigo.ProgressView();
  Indigo.offlineNoticeView = new Indigo.OfflineNoticeView();
  Indigo.errorView = new Indigo.ErrorBoxView();

  // helpers
  Indigo.toXml = function (node) {
    return new XMLSerializer().serializeToString(node);
  };
  Indigo.ga = function () {
    // google analytics are only in production
    if (window.ga) {
      ga.apply(null, arguments);
    }
  };

  // always load the user view
  Indigo.user = new Indigo.User(Indigo.Preloads.user || {
    permissions: []
  });

  window.dispatchEvent(new Event('indigo.beforecreateviews'));
}

export function createLegacyViews () {
  const Indigo = window.Indigo;

  // what views must we load?
  const views = ($('body').data('backbone-view') || '').split(' ');
  Indigo.views = _.reject(_.map(views, function (name) {
    if (name && Indigo[name]) {
      const view = new Indigo[name]();
      Indigo.view = Indigo.view || view;
      window.dispatchEvent(new CustomEvent('indigo.createview', {
        detail: {
          name: name,
          view: view
        }
      }));
      return view;
    }
  }), function (v) { return !v; });
  _.invoke(Indigo.views, 'render');

  window.dispatchEvent(new Event('indigo.viewscreated'));

  // osx vs windows
  const isOSX = navigator.userAgent.indexOf('OS X') > -1;
  document.body.classList.toggle('win', !isOSX);
  document.body.classList.toggle('osx', isOSX);

  // prevent navigating away from dirty views
  $(window).on('beforeunload', function (e) {
    if (Indigo.view && Indigo.view.isDirty && Indigo.view.isDirty()) {
      e.preventDefault();
      return $t('You will lose your changes!');
    }
  });
}
