(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.ErrorBoxView = Backbone.View.extend({
    el: $('#error-box'),
    events: {
      'click .close': 'close',
    },

    show: function(message, html) {
      var left = $(window).width()/2 - this.$el.width()/2;

      this.message = message;
      this.html = html || "";
      this.render();
      this.$el
        .css('left', left)
        .show();
    },

    close: function() {
      this.$el.hide();
    },

    render: function() {
      this.$('.message').text(this.message);
      this.$('.detail').html(this.html);
    }
  });
})(window);
