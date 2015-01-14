(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.ErrorBoxView = Backbone.View.extend({
    el: $('#error-box'),
    events: {
      'click .close': 'close',
    },

    show: function(message) {
      this.message = message;
      this.render();
      this.$el.find('.alert').removeClass('hidden');
    },

    close: function() {
      this.$el.find('.alert').addClass('hidden');
    },

    render: function() {
      this.$el.find('p').text(this.message);
    }
  });
})(window);
