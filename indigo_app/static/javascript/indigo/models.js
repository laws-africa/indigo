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
      this.on('change:dom', this.domChanged, this);
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
      // is already a change to the DOM
      if (options && options.fromXmlDocument) return;

      try {
        this.xmlDocument = $.parseXML(newValue);
      } catch(e) {
        Indigo.errorView.show("The document has invalid XML.");
        return;
      }

      this.trigger('change:dom', options);
    },

    domChanged: function(model, options) {
      // don't bother updating the content if this event was
      // originally triggered by a content change
      if (options && options.fromContent) return;

      this.set('content', this.toXml(), {fromXmlDocument: true});
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
        this.xmlDocument = first.ownerDocument;

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

      this.trigger('change:dom');
      return first;
    },

    save: function(options) {
      // When saving document contents, save all document details, so that we capture all
      // changes in a single revision on the server.
      // We do this by delegating to the document object.
      this.document.attributes.content = this.get('content');
      var result = this.document.save();
      // XXX works around https://github.com/Code4SA/indigo/issues/20 by not parsing
      // the response to the save() call
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
        country: Indigo.user.get('country_code').toLowerCase(),
      };
    },

    urlRoot: '/api/works',

    initialize: function(options) {
      // keep frbr_uri up to date
      this.on('change:country change:locality change:subtype change:number change:year', this.updateFrbrUri, this);
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
      var parts = [''];

      var country = this.get('country');
      if (this.get('locality')) {
        country += "-" + this.get('locality');
      }
      parts.push(country);
      parts.push(this.get('nature'));
      if (this.get('subtype')) {
        parts.push(this.get('subtype'));
      }
      parts.push(this.get('year'));
      parts.push(this.get('number'));

      // clean the parts
      parts = _.map(parts, function(p) { return (p || "").replace(/[ \/]/g, ''); });

      this.set('frbr_uri', parts.join('/').toLowerCase());
    },

    validate: function(attrs, options) {
      var errors = {};

      if (!attrs.title) errors.title = 'A title must be specified';
      if (!attrs.country) errors.country = 'A country must be specified';
      if (!attrs.year) errors.year = 'A year must be specified';
      if (!attrs.number) errors.number = 'A number must be specified';

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
     * Return a collection representing the amendments for this work,
     * most recent first.
     */
    amendments: function() {
      if (!this._amendments) {
        this._amendments = new Indigo.WorkAmendmentCollection([], {
          work: this,
          parse: true,
          comparator: function(a, b) {
            // most recent first
            return -(a.get('date') || '').localeCompare(b.get('date'));
          },
        });
        this.on('change:id', function(model) {
          model._amendments.fetch({reset: true});
        });
      }

      return this._amendments;
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

  Indigo.WorkAmendmentCollection = Backbone.Collection.extend({
    model: Indigo.WorkAmendment,

    initialize: function(models, options) {
      this.work = options.work;
    },

    url: function() {
      return this.work.url() + '/amendments';
    },

    parse: function(response) {
      // TODO: handle actual pagination
      return response.results ? response.results : response;
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

    setWork: function(work) {
      this.set('frbr_uri', work.get('frbr_uri'));
      this.work = work;
      this.trigger('change change:work');
    },

    /** Get the Tradition description for this document's country.
     */
    tradition: function() {
      return Indigo.traditions.get(this.get('country'));
    },
  });

  /** Create a new document by parsing an frbr URI */
  Indigo.Document.newFromFrbrUri = function(frbr_uri) {
    // /za-cpt/act/by-law/2011/foo
    var parts = frbr_uri.split('/'),
        tmp = parts[1].split('-'),
        country = tmp[0],
        locality = tmp.length > 1 ? tmp[1] : null,
        bump = parts.length > 5 ? 1 : 0;

    return new Indigo.Document({
      country: country,
      locality: locality,
      subtype: parts.length > 5 ? parts[3] : null,
      year: parts[3 + bump],
      number: parts[4 + bump],
    });
  };

  Indigo.Library = Backbone.Collection.extend({
    model: Indigo.Document,
    country: null,

    url: function() {
      var url = '/api/documents';
      var params = _.clone(this.params || {});

      if (this.country) {
        params.country = this.country;
      }

      if (params) {
        url += '?' + _.map(params, function(val, key) {
          return encodeURIComponent(key) + '=' + encodeURIComponent(val);
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
      if (this.country != country) {
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

  var showdownConverter = new showdown.Converter({
    'noHeaderId': true,
    'simplifiedAutoLink': true,
    'excludeTrailingPunctuationFromURLs': true,
    'simpleLineBreaks': true,
    'openLinksInNewWindow': true,
  });

  Indigo.Annotation = Backbone.Model.extend({
    toHtml: function() {
      return showdownConverter.makeHtml(this.get('text'));
    },
  });

  Indigo.AnnotationList = Backbone.Collection.extend({
    model: Indigo.Annotation,

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

  Indigo.DocumentActivity = Backbone.Model.extend({
    idAttribute: "nonce",
  });

})(window);
