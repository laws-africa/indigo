(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.ResetPasswordView = Backbone.View.extend({
    el: 'body',
    events: {
      'submit form': 'resetPassword',
    },

    resetPassword: function(e) {
      e.preventDefault();
      var self = this;

      var form = $('.password-reset-form');
      form.find('[name=new_password2]').val(form.find('[name=new_password1]').val());

      $.post('/auth/password/reset/confirm/', $('.password-reset-form').serialize())
        .error(function(xhr) {
          var text = "We were unable to reset your password, try resetting it from the start again.";
          var resp = xhr.responseJSON;

          if (resp.uid || resp.token) {
            text = "This password reset link has expired. Please try clicking the Forgot Password link again.";
          }

          if (resp.new_password1) {
            text = resp.new_password1;
          }

          // bad details
          $('.alert-danger').show().text(text);
        })
        .then(function(xhr) {
          // reset
          $('.password-reset-form').hide();
          $('.alert-success').show();
        });
    },
  });
})(window);
