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
      this.model = new Backbone.Collection([], {model: Indigo.DocumentActivity});
      this.listenTo(this.model, 'add remove change', this.render);

      if (this.document.get('id')) {
        this.loop();
        $(window).on('unload', _.bind(this.windowUnloaded, this));
      }
    },

    loop: function() {
      var self = this;

      function work() {
        self.markActive();
        window.setTimeout(work, 5 * 1000);
      }

      work();
    },

    markActive: function() {
      var self = this;

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
        self.model.set(resp.results);
      });
    },

    render: function() {
      var self = this;
      var items = this.model.toJSON();
      // exclude us
      items = _.filter(items, function(a) { return a.nonce != self.nonce; });

      this.$el.html(this.template({activity: items}));
    },

    windowUnloaded: function() {
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
