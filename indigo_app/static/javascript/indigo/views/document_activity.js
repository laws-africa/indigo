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

      // at the same time, we clean up finished sessions from other tabs that didn't get sent in time,
      var finished = this.getFinishedSessions(this.document.get('id')),
          nonces = _.pluck(_.values(finished), 'nonce');

      $.ajax({
        type: 'post',
        url: this.document.url() + '/activity',
        data: {
          nonce: this.nonce,
          finished_nonces: nonces.join(','),
        },
        global: false,
      }).then(function(resp) {
        Indigo.offlineNoticeView.setOnline();

        // clear the finished nonces that the server has acknowledged
        _.forEach(finished, function(data, key) {
          localStorage.removeItem(key);
        });

        // mark is_self
        resp.results.forEach(function(r) {
          r.is_self = (r.nonce == self.nonce);
        });

        self.collection.set(resp.results);
        self.collection.sort();

        // we're locked if we're not the first item in the collection
        // once locked, page must be refreshed before editing can happen
        self.locked = self.locked || !self.collection.at(0).get('is_self');
        self.render();
      }).fail(function(xhr, error) {
        if (xhr.status >= 100) {
          // we got a response from the server, we're not offline
          Indigo.offlineNoticeView.setOnline();
        } else if (xhr.status === 0 && error == 'error') {
          // couldn't make the request, we must be offline
          Indigo.offlineNoticeView.setOffline();
        }
      });
    },

    render: function() {
      var self = this,
          items = this.collection.toJSON();

      if (this.locked) {
        document.querySelector('.document-workspace-buttons .save-btn-group').innerHTML =
          items[0].is_self ?
            ('<div>You must <a href="#" onclick="window.location.reload();">refresh</a><br>before making changes.') :
            ('Editing has been locked by ' + items[0].user.display_name + '.</div>');
      }

      // exclude us
      items = _.filter(items, function(a) { return !a.is_self; });
      items.forEach(function(a) {
        a.user.colour = a.nonce.charCodeAt(0) % 8;
      });

      this.$el.html(this.template({activity: items}));
    },

    getFinishedSessions: function(document_id) {
      // look for finished sessions recorded by other tabs with their dying gasps (see windowUnloaded)
      var finished = {};

      for (var i = 0; i < localStorage.length; i++) {
        var key = localStorage.key(i);

        if (key && key.startsWith('indigo-document-activity-finished-')) {
          var data = localStorage.getItem(key);
          if (data) {
            try {
              data = JSON.parse(data);
            } catch {
              localStorage.removeItem(key);
              continue;
            }

            if (!document_id || data.document_id == document_id) {
              finished[key] = data;
            }
          }
        }
      }

      return finished;
    },

    windowUnloaded: function() {
      if (!Indigo.user.id) return;

      // store a note that this session is finished, in case we can't send this message before the window closes
      var key = 'indigo-document-activity-finished-' + this.document.get('id') + '-' + this.nonce;
      localStorage.setItem(key, JSON.stringify({
        'document_id': this.document.get('id'),
        'nonce': this.nonce,
      }));

      $.ajax({
        type: 'delete',
        url: this.document.url() + '/activity',
        data: {nonce: this.nonce},
        global: false,
        async: false,
      }).then(function() {
        localStorage.removeItem(key);
      });
    },
  });
})(window);
