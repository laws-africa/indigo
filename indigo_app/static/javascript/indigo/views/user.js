(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.UserView = Backbone.View.extend({
    el: 'body',
    events: {
      'click .js-user-buttons .btn.login.not-logged-in': 'showLoginBox',
      'click .js-user-buttons .logout': 'logout',

      // in the login modal
      'click .btn.forgot-password': 'showForgotPassword',
      'click .btn.show-login-form': 'showLoginForm',
      'show.bs.modal #login-box': 'modalShown',
      'submit form.login-form': 'authenticate',
      'submit form.forgot-password-form': 'forgotPassword',

      // user profile modal
      'show.bs.modal #user-profile-box': 'modalShown',
      'submit form.user-profile-form': 'saveUser',

      // change password modal
      'show.bs.modal #change-password-box': 'modalShown',
      'submit form.change-password-form': 'changePassword',
    },
    bindings: {
      '.username': {
        observe: ['first_name', 'email', 'username'],
        onGet: function(values) {
          return _.find(values, function(v) { return !!v; });
        }
      },
      '#profile_first_name': 'first_name',
      '#profile_last_name': 'last_name',
      '#profile_email': {
        observe: 'email',
        onSet: 'updateEmail',
      },
      '#profile_country_code': 'country_code',
    },

    initialize: function() {
      var self = this;
      var $body = $('body');

      this.model = new Indigo.User({
        username: $body.data('userUsername'),
        first_name: $body.data('userFirstName'),
      });
      this.model.on('change', this.userChanged, this);
      this.model.fetch({global: false})
        .error(function(xhr) {
          // user isn't logged in
          self.model.trigger('change');
        });

      this.stickit();

      // login modal
      this.$loginBox = $('#login-box');
      // profile modal
      this.$profileBox = $('#user-profile-box');
      // password modal
      this.$passwordBox = $('#change-password-box');
    },
    
    updateEmail: function(val, options) {
      // also set the user's username when email is set
      this.model.set('username', val);
      return val;
    },

    saveUser: function(e) {
      var self = this;
      e.preventDefault();

      this.model.save()
        .error(function(xhr) {
          self.$profileBox.find('.alert-danger').show().text("Your details could not be updated.");
        })
        .then(function() {
          self.$profileBox.modal('hide');
        });
    },

    changePassword: function(e) {
      var self = this;
      e.preventDefault();

      $.post('/auth/password/change/', this.$passwordBox.find('form').serialize())
        .error(function(xhr, status, error) {
          if (xhr.status == 400) {
            var errors = [];

            if (xhr.responseJSON.new_password1) {
              errors.push("First password: " + xhr.responseJSON.new_password1);
            }
            if (xhr.responseJSON.new_password2) {
              errors.push("Second password: " + xhr.responseJSON.new_password2);
            }

            // bad password details
            self.$passwordBox.find('.alert-danger').show().html(errors.join("<br>"));
          } else {
            self.$passwordBox.find('.alert-danger').show().text(error);
          }
        })
        .then(function(xhr) {
          // log in again automatically
          var creds = {
            'username': self.model.get('username'),
            'password': self.$passwordBox.find('[name=new_password2]').val(),
          };

          $.post('/auth/login/', creds)
            .error(function(xhr) {
              // hmm, refresh page
              window.location.reload();
            })
            .then(function(xhr) {
              self.$passwordBox.modal('hide');
              self.$passwordBox.find('form').get(0).reset();
              // update the csrf token we use
              Indigo.csrfToken = $.cookie('csrftoken');
            });
        });
    },

    modalShown: function(e) {
      $(e.currentTarget).find('.alert').hide();
      $(e.currentTarget).find('.change-password-form').each(function() { this.reset(); });
    },

    userChanged: function() {
      this.$el.find('.not-logged-in').toggle(!this.model.authenticated());
      this.$el.find('.logged-in').toggle(this.model.authenticated());
    },

    showLoginBox: function() {
      this.$loginBox.modal();
      this.$loginBox.find('.forgot-password-form').hide();
      this.$loginBox.find('.login-form').show();
    },

    showLoginForm: function(e) {
      e.preventDefault();

      this.$loginBox.find('.forgot-password-form').hide();
      this.$loginBox.find('.login-form').show();
    },

    showForgotPassword: function(e) {
      e.preventDefault();

      this.$loginBox.find('.login-form').hide();
      this.$loginBox.find('.forgot-password-form').show();
    },

    authenticate: function(e) {
      e.preventDefault();
      var self = this;

      $.post('/auth/login/', this.$loginBox.find('.login-form').serialize())
        .error(function(xhr) {
          // bad creds
          self.$loginBox.find('.alert-danger').show().text("Your username or password are incorrect.");
        })
        .then(function(xhr) {
          // logged in
          self.model.fetch()
            .then(function() {
              self.$loginBox.modal('hide');
            });
          // update the csrf token we use
          Indigo.csrfToken = $.cookie('csrftoken');
        });
    },

    forgotPassword: function(e) {
      e.preventDefault();
      var self = this;

      $.post('/auth/password/reset/', this.$loginBox.find('.forgot-password-form').serialize())
        .fail(function(xhr, msg) {
          self.$loginBox.find('.alert-danger').show().text(msg);
        })
        .then(function(xhr) {
          // reset sent
          self.$loginBox.find('.forgot-password-form').hide();
          self.$loginBox.find('.login-form').show();
          self.$loginBox.find('.alert-success').show().text('An email with password reset instructions has been sent. Please check your inbox.');
        });
    },

    logout: function() {
      var user = this.model;

      if (confirm('Are you sure you want to logout?')) {
        $.post('/auth/logout/')
          .then(function() { user.clear(); });
      }
    },
  });
})(window);
