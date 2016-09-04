(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /* A model for the content of a document. The API handles it separately
   * to the document metadata since the content can be very big.
   *
   * The model also manages an XML DOM form of the document content and keeps
   * the two in sync.
   */
  Indigo.DocumentContent = Backbone.Model.extend({
    initialize: function(options) {
      this.document = options.document;
      this.xmlDocument = null;
      this.on('change:content', this.contentChanged, this);
    },

    isNew: function() {
      // never new, always use PUT and never POST
      return false;
    },

    url: function() {
      return this.document.url() + '/content';
    },

    contentChanged: function(model, newValue, options) {
      // don't bother updating the DOM if the source of this event
      // is a change to the DOM
      if (options.fromXmlDocument) return;

      try {
        this.xmlDocument = $.parseXML(newValue);
        this.trigger('change:dom', options);
      } catch(e) {
        Indigo.errorView.show("The document has invalid XML.");
      }
    },

    // serialise an XML node, or the entire document if node is not given, to a string
    toXml: function(node) {
      return Indigo.toXml(node || this.xmlDocument);
    },

    /**
     * Replaces (or deletes) an existing node (or the whole tree) with a new node or nodes.
     * Triggers a change event.
     *
     * @param {Element} oldNode the node to replace, or null to replace the whole tree
     * @param {Element[]} newNodes the nodes to replace the old one with, or null to delete the node
     */
    replaceNode: function(oldNode, newNodes) {
      var del = !newNodes;
      var first = del ? null : newNodes[0];

      if (!oldNode || !oldNode.parentElement) {
        if (del) {
          // TODO: we don't currently support deleting whole document
          throw "Cannot currently delete the entire document.";
        }

        // entire document has changed
        if (newNodes.length != 1) {
          throw "Expected exactly one newNode, got " + newNodes.length;
        }
        console.log('Replacing whole document');
        this.xmlDocument = first;

      } else {
        if (del) {
          // delete this node
          console.log('Deleting node');
          oldNode.remove();

        } else {
          // just a fragment has changed
          console.log('Replacing node with ' + newNodes.length + ' new node(s)');

          first = oldNode.ownerDocument.importNode(first, true);
          oldNode.parentElement.replaceChild(first, oldNode);

          // now append the other nodes, starting at the end
          // because it makes the insert easier
          for (var i = newNodes.length-1; i > 0; i--) {
            var node = first.ownerDocument.importNode(newNodes[i], true);

            if (first.nextElementSibling) {
              first.parentElement.insertBefore(node, first.nextElementSibling);
            } else {
              first.parentElement.appendChild(node);
            }
          }
        }
      }

      // save the updated XML
      this.set('content', prettyPrintXml(Indigo.toXml(this.xmlDocument)), {fromXmlDocument: true});
      this.trigger('change:dom');

      return first;
    },
  });

  Indigo.Document = Backbone.Model.extend({
    defaults: {
      draft: true,
      title: '(none)',
    },

    urlRoot: '/api/documents',

    parse: function(json) {
      json.amendments = this.reifyAmendments(json.amendments);
      return json;
    },

    reifyAmendments: function(amendments) {
      // turn amendments into an AmendmentList
      if (amendments) {
        amendments = _.map(amendments, function(a) { return new Indigo.Amendment(a); });
      } else {
        amendments = [];
      }
      return new Indigo.AmendmentList(amendments);
    },

    toJSON: function() {
      var json = Backbone.Model.prototype.toJSON.apply(this, arguments);
      var amendments = this.get('amendments');

      if (amendments && amendments.toJSON) {
        json.amendments = amendments.toJSON();
      }

      return json;
    },
  });

  Indigo.Library = Backbone.Collection.extend({
    model: Indigo.Document,
    url: '/api/documents',
    parse: function(response) {
      // TODO: handle actual pagination
      return response.results;
    }
  });

  Indigo.User = Backbone.Model.extend({
    url: '/auth/user/',

    authenticated: function() {
      return !!this.get('username');
    },

    isNew: function() {
      return !this.authenticated();
    },
  });

  Indigo.Amendment = Backbone.Model.extend({});

  Indigo.AmendmentList = Backbone.Collection.extend({
    model: Indigo.Amendment,
    comparator: 'date',
  });

  Indigo.Attachment = Backbone.Model.extend({
    initialize: function() {
      this.on('sync', this.clearFile, this);
    },

    clearFile: function() {
      this.unset('file', {silent: true});
    },

    sync: function(method, model, options) {
      if (method === 'create' && model.get('file')) {
        // override params passed in for create to allow us to inject the file
        //
        // We use the FormData interface which is supported in all decent
        // browsers and IE 10+.
        //
        // https://developer.mozilla.org/en-US/docs/Web/Guide/Using_FormData_Objects
        var formData = new FormData();

        _.each(model.attributes, function(val, key) {
          formData.append(key, val);
        });

        options.data = formData;
        options.contentType = false;
      }

      return Backbone.sync.apply(this, [method, model, options]);
    },
  });

  Indigo.AttachmentList = Backbone.Collection.extend({
    model: Indigo.Attachment,
    comparator: 'filename',

    initialize: function(models, options) {
      this.document = options.document;
    },

    url: function() {
      return this.document.url() + '/attachments';
    },

    parse: function(response) {
      // TODO: handle actual pagination
      return response.results;
    },

    save: function(options) {
      var self = this;

      // save each object individually
      return $
        .when.apply($, this.map(function(obj) {
          return obj.save(null, {silent: true});
        }))
        .done(function() {
          self.trigger('saved');
        });
    },
  });

  Indigo.Revision = Backbone.Model.extend({});

  Indigo.RevisionList = Backbone.Collection.extend({
    model: Indigo.Revision,
    comparator: 'date',
  });

  Indigo.RevisionList = Backbone.Collection.extend({
    model: Indigo.Revision,
    comparator: 'filename',

    initialize: function(models, options) {
      this.document = options.document;
    },

    url: function() {
      return this.document.url() + '/revisions';
    },

    parse: function(response) {
      // TODO: handle actual pagination
      return response.results;
    },
  });

})(window);
