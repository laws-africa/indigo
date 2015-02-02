(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.UserView = Backbone.View.extend({
    el: 'body',
    events: {
      'click .js-user-buttons .btn.login.not-logged-in': 'showLoginBox',
      'click .js-user-buttons .logout': 'logout',

      // in the modal
      'click .btn.forgot-password': 'showForgotPassword',
      'show.bs.modal #login-box': 'loginBoxShown',
      'submit form.login-form': 'authenticate',
      'submit form.forgot-password-form': 'forgotPassword',
    },
    bindings: {
      '.username': 'first_name',
    },

    initialize: function() {
      var self = this;

      this.model = new Indigo.User();
      this.model.on('change', this.userChanged, this);
      this.model.fetch()
        .error(function(xhr) {
          // user isn't logged in
          self.model.trigger('change');
        });

      this.stickit();

      // login modal
      this.$loginBox = $('#login-box');
    },

    loginBoxShown: function() {
      this.$loginBox.find('.alert').hide();
    },

    userChanged: function() {
      this.$el.find('.not-logged-in').toggle(!this.model.authenticated());
      this.$el.find('.logged-in').toggle(this.model.authenticated());
    },

    showLoginBox: function() {
      this.$loginBox.modal();
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
