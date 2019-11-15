(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handles the "offline" notice globally.
   */
  Indigo.OfflineNoticeView = Backbone.View.extend({
    el: '#offline-alert',

    autoShow: function() {
      $(document).on('offline', _.bind(this.setOffline, this));
      $(document).on('online', _.bind(this.setOnline, this));
      if (!navigator.onLine) this.show();
    },

    setOnline: function() {
      this.hide();
    },

    setOffline: function() {
      this.show();
    },

    show: function() {
      this.$el.removeClass('d-none');
    },

    hide: function() {
      this.$el.addClass('d-none');
    },
  });
})(window);
