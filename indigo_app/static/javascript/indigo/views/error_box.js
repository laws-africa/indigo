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
      var left = $(window).width()/2 - this.$el.width()/2;

      this.message = message;
      this.render();
      this.$el
        .css('left', left)
        .removeClass('hidden');
    },

    close: function() {
      this.$el
        .addClass('hidden');
    },

    render: function() {
      this.$el.find('p').text(this.message);
    }
  });
})(window);
