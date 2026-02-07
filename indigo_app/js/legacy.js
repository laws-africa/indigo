export function setupLegacyAjax () {
  const Indigo = window.Indigo;

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
}
