(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.UserView = Backbone.View.extend({
    el: '.js-user-buttons',
    events: {
      'click .login.not-logged-in': 'showLoginBox',
      'click .logout': 'logout',
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

      this.$loginBox = $('#login-box');
      this.$loginBox
        .on('show.bs.modal', function() {
          self.$loginBox.find('.alert').hide();
        })
        .find('form').on('submit', _.bind(this.authenticate, this));
    },

    userChanged: function() {
      this.$el.find('.not-logged-in').toggle(!this.model.authenticated());
      this.$el.find('.logged-in').toggle(this.model.authenticated());
    },

    showLoginBox: function() {
      this.$loginBox.modal();
    },

    authenticate: function(e) {
      e.preventDefault();
      var self = this;

      $.post('/auth/login/', this.$loginBox.find('form').serialize())
        .error(function(xhr) {
          // bad creds
          self.$loginBox.find('.alert').show();
          self.$loginBox.find('.alert').text("Your username or password are incorrect.");
        })
        .then(function(xhr) {
          // logged in
          self.model.fetch();
          self.$loginBox.modal('hide');
          // update the csrf token we use
          Indigo.csrfToken = $.cookie('csrftoken');
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
