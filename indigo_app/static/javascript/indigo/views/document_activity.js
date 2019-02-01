(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handle the document activity viewer.
   */
  Indigo.DocumentActivityView = Backbone.View.extend({
    el: '#document-activity-view',
    template: '#document-activity-template',

    initialize: function(options) {
      this.template = Handlebars.compile($(this.template).html());

      this.document = options.document;
      this.collection = new Backbone.Collection([], {
        model: Indigo.DocumentActivity,
        comparator: 'created_at',
      });
      this.listenTo(this.collection, 'add remove change', this.render);

      if (this.document.get('id')) {
        this.loop();
        $(window).on('unload', _.bind(this.windowUnloaded, this));
      }
    },

    loop: function() {
      var self = this;

      function work() {
        self.markActive();
        // ping the server every few seconds to tell them we're alive
        window.setTimeout(work, 10 * 1000);
      }

      work();
    },

    markActive: function() {
      var self = this;

      if (!Indigo.user.id) return;

      if (!this.nonce) {
        var min = 1000,
            max = 1000000;
        this.nonce = Math.floor(Math.random() * (max - min) + min).toString();
      }

      $.ajax({
        type: 'post',
        url: this.document.url() + '/activity',
        data: {nonce: this.nonce},
        global: false,
      }).then(function(resp) {
        self.collection.set(resp.results);
        self.collection.sort();
      });
    },

    render: function() {
      var self = this;
      var items = this.collection.toJSON();
      // exclude us
      items = _.filter(items, function(a) { return a.nonce != self.nonce; });
      items.forEach(function(a) {
        a.user.colour = a.nonce.charCodeAt(0) % 8;
      });

      this.$el.html(this.template({activity: items}));
    },

    windowUnloaded: function() {
      if (!Indigo.user.id) return;

      $.ajax({
        type: 'delete',
        url: this.document.url() + '/activity',
        data: {nonce: this.nonce},
        global: false,
        async: false,
      });
    },
  });
})(window);
