(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  function escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  /**
   * A model for the content of a document. The API handles it separately to the document metadata since the content
   * can be very big.
   *
   * The model also manages an XML DOM form of the document content, and updates the DOM if the text content changes.
   * The reverse is not true: the text content is not kept up to date for performance reasons. If the text content
   * is required, it must first be serialised with toXml().
   *
   * This model fires custom events:
   *
   * - mutation - when the XML DOM is manipulated by any means, based on the MutationObserver class. The parameter
   *              for the event is list of MutationRecord objects.
   * - change:dom - when the XML DOM is manipulated by any means, after all the mutation events have been fired.
   */
  Indigo.DocumentContent = Backbone.Model.extend({
    initialize: function(options) {
      this.document = options.document;
      this.document.content = this;
      this.xmlDocument = null;
      this.observer = null;
      this.on('change:content', this.contentChanged, this);
    },

    isNew: function() {
      // never new, always use PUT and never POST
      return false;
    },

    url: function() {
      return this.document.url() + '/content';
    },

    setupMutationObserver: function () {
      this.observer = new MutationObserver((mutations) => {
        console.log('mutations', mutations);
        this.trigger('mutation', this, mutations);
        this.trigger('change:dom', this);
        this.trigger('change', this);
      });

      this.observer.observe(this.xmlDocument, {
        childList: true,
        attributes: true,
        subtree: true,
      });
    },

    /**
     * Determine the impact of a mutation on the provided element.
     * @param mutation MutationRecord
     * @param element Element in this XML document
     * @returns 'changed' if the mutation impacts the element, 'removed' if the element was removed from the tree,
     *          'replaced', if the element has been replaced (with a node in mutation.addedNodes),
     *          or null if there is no impact
     */
    getMutationImpact(mutation, element) {
      const target = mutation.target;

      if (mutation.type === 'childList') {
        if (mutation.removedNodes[0] === element) {
          if (mutation.addedNodes.length === 0) {
            // the element itself was removed
            return 'removed';
          }

          // the element has been replaced
          return 'replaced';
        }

        if (!this.xmlDocument.contains(element)) {
          // the change removed xmlElement from the tree
          return 'removed';
        }
      }

      if (target === element || element.contains(target)) {
        // the mutated node is xmlElement itself or one of its descendants
        return 'changed';
      }

      // we don't care about attribute or character data changes elsewhere in the document
    },

    contentChanged: function(model, newValue, options) {
      let root = null;

      try {
        root = Indigo.parseXml(newValue);
      } catch(e) {
        Indigo.errorView.show("The document has invalid XML.");
        return;
      }

      if (!this.xmlDocument) {
        this.xmlDocument = root;
        this.setupMutationObserver();
        this.trigger('change:dom', this);
        this.trigger('change', this);
      } else {
        root = root.documentElement;
        this.xmlDocument.adoptNode(root);
        this.xmlDocument.documentElement.replaceWith(root);
      }

      // clear the content, so that any change later will always trigger a change event, because we don't keep
      // the content synced with the changes in the DOM
      this.set('content', '', {silent: true});
    },

    /**
     * Rewrite all eIds and component names to ensure they are correct. This should be done after the DOM structure
     * is changed.
     */
    rewriteIds: function() {
      // rewrite all eIds before setting the content
      // in provision mode, retain the eId of the parent element as the prefix
      // and use the counters of all preceding provisions for context
      let eidPrefix,
          eidRewriter = new indigoAkn.EidRewriter(),
          workComponentRewriter = new indigoAkn.WorkComponentRewriter();
      if (Indigo.Preloads.provisionEid && Indigo.Preloads.provisionEid.lastIndexOf('__') > -1) {
        eidPrefix = Indigo.Preloads.provisionEid.substring(0, Indigo.Preloads.provisionEid.lastIndexOf('__'));
      }
      if (Indigo.Preloads.provisionEid) {
        eidRewriter.counters = JSON.parse(JSON.stringify(Indigo.Preloads.provisionCounters));
        eidRewriter.eIdCounter = JSON.parse(JSON.stringify(Indigo.Preloads.eidCounter));
        workComponentRewriter.counters = JSON.parse(JSON.stringify(Indigo.Preloads.attachmentCounters));
      }
      eidRewriter.rewriteEid(this.xmlDocument.documentElement, eidPrefix);
      // rewrite all attachment FRBR URI work components too
      workComponentRewriter.rewriteAttachmentWorkComponent(this.xmlDocument.documentElement);
    },

    // serialise an XML node, or the entire document if node is not given, to a string
    toXml: function(node) {
      return Indigo.toXml(node || this.xmlDocument);
    },

    // in provision mode, wrap serialized XML in akn tags
    wrapInAkn: function (xml) {
      if (Indigo.Preloads.provisionEid) {
        xml = `<akomaNtoso xmlns="${this.xmlDocument.firstChild.getAttribute('xmlns')}">${xml}</akomaNtoso>`;
      }
      return xml;
    },

    // serialise the absolute basics of the document for server-side XML manipulation
    toSimplifiedJSON: function() {
      return {
        "xml": this.wrapInAkn(this.toXml()),
        "language": this.document.attributes.language,
        "provision_eid": Indigo.Preloads.provisionEid
      };
    },

    /**
     * Replaces (or deletes) an existing node (or the whole tree) with a new node or nodes.
     * Triggers a change event.
     *
     * @param {Element} oldNode the node to replace, or null to replace the whole tree
     * @param {Element[]} newNodes the nodes to replace the old one with, or null to delete the node
     */
    replaceNode: function(oldNode, newNodes) {
      try {
        let fixes = indigoAkn.fixTables(newNodes || []);
        if (fixes.length) {
          Indigo.errorView.show("These tables have been fixed:", "<ul><li>" + fixes.join("</li><li>") + "</li></ul>");
        }
      } catch (e) {
        Indigo.errorView.show(e);
        return;
      }
      var del = !newNodes;
      var first = del ? null : newNodes[0];

      if (oldNode && !this.xmlDocument.contains(oldNode)) {
        console.log('Old node is not in the document');
        return;
      }

      if (!oldNode || !oldNode.parentElement) {
        if (del) {
          throw "Cannot currently delete the entire document.";
        }

        // entire document has changed
        if (newNodes.length !== 1) {
          throw "Expected exactly one newNode, got " + newNodes.length;
        }
        this.xmlDocument.adoptNode(first);
        // mutation record will have both add and remove in one record (a replace)
        this.xmlDocument.documentElement.replaceWith(first);

      } else {
        if (del) {
          // delete this node
          console.log('Deleting node');
          // mutation record will have a remove
          oldNode.remove();

        } else {
          // just a fragment has changed
          console.log('Replacing node with ' + newNodes.length + ' new node(s)');

          oldNode.ownerDocument.adoptNode(first);
          // mutation record will have both add and remove in one record (a replace)
          oldNode.parentElement.replaceChild(first, oldNode);

          // now append the other nodes, starting at the end
          // because it makes the insert easier
          for (var i = newNodes.length-1; i > 0; i--) {
            const node = newNodes[i];
            first.ownerDocument.adoptNode(node);

            if (first.nextElementSibling) {
              // mutation record will have an add
              first.parentElement.insertBefore(node, first.nextElementSibling);
            } else {
              // mutation record will have an add
              first.parentElement.appendChild(node);
            }
          }
        }
      }

      this.rewriteIds();

      return first;
    },

    /** Evaluate an xpath expression on this document, using the namespace prefix 'a'.
     */
    xpath: function(expression, context, result) {
      var ns = {
        a: this.xmlDocument.lookupNamespaceURI(''),
      };

      if (result === undefined) result = XPathResult.ORDERED_NODE_SNAPSHOT_TYPE;
      if (context === undefined) context = this.xmlDocument.getRootNode();

      function nsLookup(x) {
        return ns[x];
      }
      return this.xmlDocument.evaluate(expression, context, nsLookup, result);
    },

    /** Get an element by id, which is potentially scoped to a component (eg. "schedule1/table-1").
     * @param scopedId
     */
    getElementByScopedId: function(scopedId) {
      var node = this.xmlDocument;

      scopedId.split("/").forEach(function(id) {
        node = node.querySelector('[eId="' + id + '"]');
      });

      return node;
    },

    save: function(options) {
      // When saving document contents, save all document details, so that we capture all
      // changes in a single revision on the server.
      // We do this by delegating the actual save to the document object.

      // serialise the xml from the live DOM
      this.document.attributes.content = this.wrapInAkn(this.toXml());
      this.document.attributes.provision_eid = Indigo.Preloads.provisionEid;
      const result = this.document.save();
      // don't re-parse the content in the response to the save() call
      delete this.document.attributes.content;
      this.document.setClean();
      this.trigger('sync');

      return result;
    },
  });

  Indigo.Work = Backbone.Model.extend({
    defaults: function() {
      return {
        nature: 'act',
        country: Indigo.user.id ? Indigo.user.get('country_code').toLowerCase() : null,
      };
    },

    urlRoot: '/api/works',

    initialize: function(options) {
      // keep frbr_uri up to date
      this.on('change:country change:locality change:nature change:subtype change:actor change:number change:date', this.updateFrbrUri, this);
    },

    parse: function(json) {
      if (json.commencing_work) json.commencing_work = new Indigo.Work(json.commencing_work);
      if (json.repealed_by) json.repealed_by = new Indigo.Work(json.repealed_by);
      if (json.parent_work) json.parent_work = new Indigo.Work(json.parent_work);
      return json;
    },

    toJSON: function() {
      var json = Backbone.Model.prototype.toJSON.apply(this, arguments);
      if (json.commencing_work && json.commencing_work.toJSON) json.commencing_work = json.commencing_work.toJSON();
      if (json.repealed_by && json.repealed_by.toJSON) json.repealed_by = json.repealed_by.toJSON();
      if (json.parent_work && json.parent_work.toJSON) json.parent_work = json.parent_work.toJSON();
      return json;
    },

    updateFrbrUri: function() {
      // rebuild the FRBR uri when one of its component sources changes
      var parts = ['', 'akn'];

      var country = this.get('country');
      if (this.get('locality')) {
        country += "-" + this.get('locality');
      }
      parts.push(country);
      parts.push(this.get('nature'));
      if (this.get('subtype')) {
        parts.push(this.get('subtype'));
      }
      if (this.get('actor')) {
        parts.push(this.get('actor'));
      }
      parts.push(this.get('date'));
      parts.push(this.get('number'));

      // clean the parts
      parts = _.map(parts, function(p) { return (p || "").replace(/[ /]/g, ''); });

      this.set('frbr_uri', parts.join('/').toLowerCase());
    },

    validate: function(attrs, options) {
      var errors = {};

      if (!attrs.title) errors.title = $t('A title must be specified');
      if (!attrs.country) errors.country = $t('A country must be specified');
      if (!attrs.date) errors.date = $t('A year (or date) must be specified');
      if (!attrs.number) errors.number = $t('A number must be specified');

      if (!_.isEmpty(errors)) return errors;
    },

    /**
     * Return a collection of all the documents linked to this work
     */
    documents: function() {
      if (!this._documents) {
        var self = this;
        var docs = this._documents = new Indigo.Library();

        var repopulate = function() {
          docs.reset(Indigo.library.where({frbr_uri: self.get('frbr_uri')}));
        };

        docs.on('add remove', repopulate);
        this.on('change:frbr_uri', repopulate);
        repopulate();
      }

      return this._documents;
    },

    /**
     * Get a sorted array of dates of available expressions (documents) of this work.
     */
    expressionDates: function() {
      return _.uniq(this.documents().pluck('expression_date')).sort();
    },
  });

  Indigo.WorkAmendment = Backbone.Model.extend({
    parse: function(json) {
      json.amending_work = new Indigo.Work(json.amending_work);
      return json;
    },

    toJSON: function() {
      var json = Backbone.Model.prototype.toJSON.apply(this, arguments);
      json.amending_work = this.get('amending_work').toJSON();
      return json;
    },
  });

  Indigo.Document = Backbone.Model.extend({
    defaults: {
      draft: true,
      title: '(none)',
      nature: 'act',
    },

    urlRoot: '/api/documents',

    initialize: function(options) {
      this.dirty = false;

      // this is useful to know when the model needs to be saved
      this.on('change', this.setDirty, this);
      this.on('sync', this.setClean, this);
    },

    setDirty: function() {
      this.dirty = true;
    },

    setClean: function() {
      this.dirty = false;
    },

    parse: function(json) {
      var self = this;

      json.amendments = this.reifyAmendments(json.amendments);

      // ensure that changes to amendments fire model changes
      this.listenTo(json.amendments, 'change add remove', function() {
        self.trigger('change change:amendments');
      });

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

    attachments: function() {
      if (!this.attachmentList) {
        this.attachmentList = new Indigo.AttachmentList(null, {document: this});

        if (this.get('id')) {
          this.attachmentList.fetch({reset: true});
        } else {
          this.attachmentList.reset([]);
        }
      }

      return this.attachmentList;
    },

    /**
     * Build and return a fully qualified manifestation URL for this document.
     */
    manifestationUrl: function() {
      var url = window.location.origin;

      if (this.get('draft')) {
        url = url + this.url();

      } else {
        // full published url
        url = url + "/api" + this.get('frbr_uri') + '/' + this.get('language');
        if (this.get('expression_date')) {
          url = url + '@' + this.get('expression_date');
        }
      }

      return url;
    },

    /** Get the Tradition description for this document's country.
     */
    tradition: function() {
      return Indigo.traditions.get(this.get('country'));
    },

    /** Get a live AnnotationList for this document.
     */
    annotations: function() {
      if (!this._annotations) {
        this._annotations = new Indigo.AnnotationList([], {document: this});
        this._annotations.fetch({reset: true});
      }
      return this._annotations;
    },

    /** Get a live AnnotationThreadList for this document.
     */
    annotationThreads: function() {
      if (!this._annotationThreads) {
        this._annotationThreads = new Indigo.AnnotationThreadList([], {annotations: this.annotations()});
      }
      return this._annotationThreads;
    }
  });

  Indigo.Library = Backbone.Collection.extend({
    model: Indigo.Document,
    country: null,

    initialize: function(options) {
      this.params = (options || {}).params || {};
    },

    url: function() {
      var url = '/api/documents';
      var params = _.clone(this.params || {});

      if (this.country) {
        params.country = this.country;
      }

      if (params) {
        url += '?' + _.map(params, function(val, key) {
          return encodeURIComponent(key) + '=' + encodeURIComponent(val === null ? '' : val);
        }).join('&');
      }

      return url;
    },

    parse: function(response) {
      // TODO: handle actual pagination
      return response.results;
    },

    setParams: function(params) {
      this.params = params;
      return this.fetch({reset: true});
    },

    setCountry: function(country) {
      if (this.country != country) {
        this.country = country;
        return this.fetch({reset: true});
      }
      return $.Deferred().resolve();
    },
  });

  Indigo.WorksCollection = Backbone.Collection.extend({
    model: Indigo.Work,
    country: null,
    next_page: null,
    base_url: '/api/works',
    params: {},

    url: function() {
      var url = this.base_url;
      var params = _.clone(this.params || {});

      params.country = this.country;
      url += '?' + _.map(params, function(val, key) {
        return encodeURIComponent(key) + '=' + encodeURIComponent(val);
      }).join('&');

      return url;
    },

    parse: function(response, options) {
      var items = response.results;
      this.next_page = response.next;

      if (options.incremental) {
        // loading next page, add in previous models
        items = _.map(options.previousModels, function(m) { return m.toJSON(); });
        items = items.concat(response.results);
      }

      return items;
    },

    setCountry: function(country) {
      if (this.country !== country) {
        this.country = country;
        return this.fetch({reset: true});
      }
      return $.Deferred().resolve();
    },

    hasNextPage: function() {
      return !!this.next_page;
    },

    getNextPage: function() {
      return this.fetch({url: this.next_page, incremental: true, reset: true});
    }
  });

  Indigo.User = Backbone.Model.extend({
    url: '/api/auth/user/',

    authenticated: function() {
      return !!this.get('username');
    },

    isNew: function() {
      return !this.authenticated();
    },

    hasPerm: function(perm) {
      return this.get('permissions').indexOf(perm) > -1;
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
      this.listenTo(this, 'change:filename', this.sort);
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

  Indigo.Annotation = Backbone.Model.extend({
    toHtml: function() {
      var text = escapeHtml(this.get('text'));

      // split on newlines and wrap each line in a <p> tag
      return "<p>" + text.replace(/\n+/g, "</p><p>") + "</p>";
    },

    parse: function(json) {
      if (json.task) json.task = new Backbone.Model(json.task);
      return json;
    },

    createTask: function() {
      var self = this;
      $.post(this.url() + '/task')
        .then(function(task) {
          self.set('task', new Backbone.Model(task));
        });
    },
  });

  Indigo.AnnotationList = Backbone.Collection.extend({
    model: Indigo.Annotation,
    comparator: 'created_at',

    initialize: function(models, options) {
      this.document = options.document;
    },

    parse: function(response) {
      // TODO: handle actual pagination
      return response.results;
    },

    url: function() {
      return this.document.url() + '/annotations';
    },
  });

  /**
   * A thread of annotations, with at least one annotation (the root).
   */
  Indigo.AnnotationThread = Backbone.Model.extend({
    initialize: function(attribs, options) {
      this.document = options.document;
      this.annotations = new Backbone.Collection(options.annotations, { comparator: 'created_at' });
      this.root().on('destroy', this.destroyed.bind(this));
    },

    root: function() {
      return this.annotations.first();
    },

    /** Add a new annotation to this thread.
     */
    add: function(attribs) {
      attribs.in_reply_to = this.root().get('id');
      attribs.anchor_id = this.root().get('anchor_id');
      const anntn = new Indigo.Annotation(attribs);

      // add it to the master annotation list
      this.document.annotations().add(anntn);
      // add it to our local thread list
      this.annotations.add(anntn);

      return anntn;
    },

    destroyed: function() {
      // root was destroyed, delete everything else
      const root = this.root();
      const annotations = this.annotations;
      annotations.forEach(a => {
        if (a !== root && a) {
          a.destroy();
        }
      });
      this.trigger('destroy');
    }
  });

  /**
   * Collection that groups a documents annotations into threads, and
   * manages the creation/removal of threads.
   */
  Indigo.AnnotationThreadList = Backbone.Collection.extend({
    initialize: function(models, options) {
      this.document = options.annotations.document;
      this.annotations = options.annotations;
      this.annotations.on('reset', this.prepare.bind(this));
      this.prepare();
    },

    prepare: function() {
      // group annotations by thread
      const groups = Object.values(this.annotations.groupBy(a => a.get('in_reply_to') || a.get('id')));
      this.reset(groups.map(g => this.makeThread(g)));
    },

    /**
     * Start a new thread using the given attributes for the root annotation.
     */
    createThread: function(attribs) {
      const root = this.annotations.add(attribs);
      const thread = this.makeThread([root]);
      this.add(thread);
      return thread;
    },

    makeThread: function(annotations) {
      const thread = new Indigo.AnnotationThread({}, {annotations: annotations, document: this.document});
      const root = thread.root();

      // monitor the thread: if the root annotation is deleted, remove this thread from the collection
      thread.on('remove', e => {
        if (e === root) {
          // root annotation has been deleted, remove this thread
          this.remove(thread);
        }
      });

      return thread;
    }
  });

  Indigo.DocumentActivity = Backbone.Model.extend({
    idAttribute: "nonce",
  });

})(window);
