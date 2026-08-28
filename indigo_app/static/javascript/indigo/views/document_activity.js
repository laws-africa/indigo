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
          r.is_self = (r.nonce === self.nonce);
        });

        self.collection.set(resp.results);
        self.collection.sort();

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
      var items = this.collection.toJSON();

      // exclude us
      items = _.filter(items, function(a) { return !a.is_self; });
      items.forEach(function(a) {
        a.user.colour = a.nonce.charCodeAt(0) % 8;
        a.has_edit_lease = items.length > 0 && a.has_edit_lease;
      });

      // Heartbeats update timestamps and lease renewals update state, but
      // neither normally changes what is visible. Avoid replacing the badges
      // unless their rendered content has actually changed.
      const renderKey = JSON.stringify(items.map(function(a) {
        return [a.nonce, a.user.id, a.user.display_name, a.is_asleep, a.has_edit_lease];
      }));
      if (renderKey === this.renderKey) return;
      this.renderKey = renderKey;

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
            } catch(err) {
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

  /** Manage the exclusive, versioned lease used while editing a document. */
  Indigo.DocumentEditLease = Backbone.Model.extend({
    initialize: function(options) {
      this.document = options.document;
      this.document.editLease = this;
      this.held = false;
      this.pending = null;
      this.renewTimer = null;
      this.acquireRetryTimer = null;
      this.saving = false;
      this.state = 'viewing';
      this.storageKey = 'indigo-document-edit-lease-' + this.document.get('id');

      const stored = sessionStorage.getItem(this.storageKey);
      if (stored) {
        try {
          const data = JSON.parse(stored);
          this.token = data.token;
          this.clientId = data.client_id;
        } catch (e) {
          sessionStorage.removeItem(this.storageKey);
        }
      }
      this.clientId = this.clientId || this.newId();
      this.pageId = this.newId();
      this.setupTabCoordination();

      // A refresh may resume its lease. A newly opened document has no stored
      // token and therefore remains a presence-only viewer.
      if (this.token) {
        if (this.tabChannel) {
          this.duplicateLeasePage = false;
          this.tabChannel.postMessage({
            type: 'probe',
            client_id: this.clientId,
            page_id: this.pageId,
          });
          window.setTimeout(() => {
            if (!this.duplicateLeasePage) this.acquire();
          }, 150);
        } else {
          this.acquire();
        }
      }
      document.addEventListener('visibilitychange', () => {
        if (this.held && document.visibilityState === 'visible') this.acquire(true);
      });
    },

    newId: function() {
      if (window.crypto && window.crypto.randomUUID) return window.crypto.randomUUID();
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
      });
    },

    setupTabCoordination: function() {
      if (!window.BroadcastChannel) return;
      this.tabChannel = new window.BroadcastChannel(
        'indigo-document-edit-lease-' + this.document.get('id')
      );
      this.tabChannel.onmessage = (event) => {
        const message = event.data || {};
        if (message.type === 'probe' && this.held && message.client_id === this.clientId) {
          this.tabChannel.postMessage({
            type: 'active',
            client_id: this.clientId,
            page_id: message.page_id,
          });
        } else if (message.type === 'active' && message.page_id === this.pageId) {
          this.duplicateLeasePage = true;
          this.held = false;
          this.clearStoredLease();
        }
      };
    },

    url: function() {
      return this.document.url() + '/edit-lease';
    },

    setState: function(state, details) {
      this.state = state;
      if (details !== undefined) this.stateDetails = details;
      this.trigger('state', state, details);
    },

    acquire: function(force) {
      if (this.held && !force && !this.pending) return $.Deferred().resolve(this.toJSON());
      if (this.pending) return this.pending;

      const data = {
        expected_updated_at: this.document.get('updated_at'),
        client_id: this.clientId,
      };
      if (this.token) data.token = this.token;

      this.setState(this.held ? 'renewing' : 'acquiring');
      this.pending = $.ajax({
        type: 'post',
        url: this.url(),
        data: data,
        global: false,
      });
      this.pending.done((response) => {
        this.set(response);
        this.token = response.token;
        this.clientId = response.client_id;
        // Base the local deadline on the lease duration rather than the
        // browser clock, which may differ from the server clock.
        this.expiresAt = Date.now() + (
          new Date(response.expires_at).getTime() - new Date(response.renewed_at).getTime()
        );
        this.held = true;
        window.clearTimeout(this.acquireRetryTimer);
        this.setState('editing', response);
        sessionStorage.setItem(this.storageKey, JSON.stringify({
          token: this.token,
          client_id: this.clientId,
        }));
        this.scheduleRenewal(response.renew_after_seconds);
      });
      this.pending.fail((xhr) => this.handleFailure(xhr));
      this.pending.always(() => {
        this.pending = null;
      });
      return this.pending;
    },

    scheduleRenewal: function(seconds) {
      window.clearTimeout(this.renewTimer);
      this.renewTimer = window.setTimeout(() => {
        if (this.saving) {
          this.scheduleRenewal(5);
        } else {
          this.acquire(true);
        }
      }, (seconds || 20) * 1000);
    },

    prepareToSave: async function() {
      if (this.pending) {
        try {
          await Indigo.deferredToAsync(this.pending);
        } catch (e) {
          return false;
        }
      }
      if (!this.held) return false;
      this.saving = this.held;
      window.clearTimeout(this.renewTimer);
      return this.held;
    },

    saveFinished: function() {
      this.saving = false;
      if (this.held) this.scheduleRenewal(this.get('renew_after_seconds'));
    },

    handleFailure: function(xhr) {
      const response = xhr.responseJSON || {};
      if (xhr.status === 0 && this.held && Date.now() < this.expiresAt) {
        Indigo.offlineNoticeView.setOffline();
        this.scheduleRenewal(5);
        return;
      }
      if (response.code === 'document_locked') {
        this.held = false;
        this.clearStoredLease();
        this.setState('locked', response);
        const expiresAt = new Date(response.expires_at).getTime();
        const retryAfter = Math.max(1000, Math.min(10000, expiresAt - Date.now() + 250));
        this.scheduleAcquisitionRetry(retryAfter);
      } else if (response.code === 'document_changed' || response.code === 'edit_lease_lost') {
        this.lose(response);
      } else if (this.held) {
        response.detail = $t('Saving is unavailable because the editing lease could not be renewed.');
        this.lose(response);
      } else {
        this.setState('viewing', response);
        this.scheduleAcquisitionRetry(5000);
      }
    },

    scheduleAcquisitionRetry: function(milliseconds) {
      window.clearTimeout(this.acquireRetryTimer);
      this.acquireRetryTimer = window.setTimeout(() => {
        if (!this.held && this.state !== 'stale') this.acquire();
      }, milliseconds);
    },

    lose: function(response) {
      this.held = false;
      this.saving = false;
      window.clearTimeout(this.renewTimer);
      this.clearStoredLease();
      this.setState(response && response.code === 'document_changed' ? 'stale' : 'lost', response);
      if (!response || response.code !== 'document_changed') this.scheduleAcquisitionRetry(1000);
    },

    clearStoredLease: function() {
      this.token = null;
      sessionStorage.removeItem(this.storageKey);
    },
  });
})(window);
