(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handles the progress bar globally.
   */
  Indigo.ProgressView = Backbone.View.extend({
    el: '#progress-bar',
    stack: 0,

    peg: function() {
      this.pegged = true;
      this.render();
    },

    unpeg: function() {
      this.pegged = false;
      this.render();
    },

    push: function() {
      this.stack += 1;
      this.render();
    },

    pop: function() {
      this.stack -= 1;
      this.render();
    },

    render: function() {
      this.$el.toggle(this.pegged || this.stack > 0);
    },
  });
})(window);
