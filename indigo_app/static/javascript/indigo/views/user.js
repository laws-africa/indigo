(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.UserView = Backbone.View.extend({
    el: 'body',
    events: {
      'click #user-buttons .logout': 'logout',

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
      this.$el.toggleClass('authenticated', this.model.authenticated());
      this.$el.toggleClass('unauthenticated', !this.model.authenticated());
      this.$el.toggleClass('is-staff', this.model.get('is_staff'));
    },

    logout: function() {
      var user = this.model;

      if (confirm('Are you sure you want to logout?')) {
        $.post('/auth/logout/')
          .then(function() { window.location = '/user/login/'; });
      }
    },
  });
})(window);
