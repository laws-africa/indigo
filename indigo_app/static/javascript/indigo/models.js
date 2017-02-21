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

    save: function(options) {
      // When saving document contents, save all document details, so that we capture all
      // changes in a single revision on the server.
      // We do this by delegating to the document object.
      this.document.attributes.content = this.get('content');
      this.document.save();
      // XXX works around https://github.com/Code4SA/indigo/issues/20 by not parsing
      // the response to the save() call
      delete this.document.attributes.content;
      this.document.setClean();
      this.trigger('sync');
    },
  });

  Indigo.Document = Backbone.Model.extend({
    defaults: {
      draft: true,
      title: '(none)',
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
  });

  Indigo.Library = Backbone.Collection.extend({
    model: Indigo.Document,
    url: '/api/documents',
    parse: function(response) {
      // TODO: handle actual pagination
      return response.results;
    },

    /**
     * Return an ExpressionSet for the collection of documents for +frbr_uri+.
     */
    expressionSet: function(document) {
      if (!document.expressionSet) {
        document.expressionSet = new Indigo.ExpressionSet(null, {
          library: this,
          frbr_uri: document.get('frbr_uri'),
          follow: document,
        });
      }

      return document.expressionSet;
    },
  });

  /**
   * A collection of documents that are all expressions of the same work, based
   * on the frbr_uri. Updated dynamically as document URIs change.
   */
  Indigo.ExpressionSet = Backbone.Collection.extend({
    model: Indigo.Document,
    comparator: 'expression_date',

    initialize: function(models, options) {
      this.frbr_uri = options.frbr_uri;
      this.library = options.library;

      // update ourselves if the document library changes
      this.listenTo(this.library, 'reset add remove', this.build);
      this.listenTo(this.library, 'change:frbr_uri', this.checkFrbrUriChange);

      // watch documents for changed expression dates
      this.on('change:expression_date', this.alignDocumentAmendments, this);

      // should we follow a particular document even if its frbr_uri changes?
      if (options.follow) {
        this.listenTo(options.follow, 'change:frbr_uri', this.followingFrbrUriChanged, this);
      }

      this.amendments = new Backbone.Collection();
      this.listenTo(this.amendments, 'remove', this.amendmentRemoved);
      // when an amendment is added, ensure all docs have their amendments updated
      this.listenTo(this.amendments, 'add', this.alignAllDocumentAmendments);
      this.listenTo(this.amendments, 'change:date', this.amendmentDateChanged);

      this.build();
    },

    build: function() {
      this.reset(this.library.where({frbr_uri: this.frbr_uri}));

      // build up a unique collection of amendments
      var amendments = _.inject(this.models, function(memo, doc) {
        if (doc.get('amendments')) {
          memo = memo.concat(doc.get('amendments').models);
        }
        return memo;
      }, []);
      amendments = _.uniq(amendments, false, function(a) {
        return a.get('amending_uri');
      });
      this.amendments.reset(amendments);
    },

    followingFrbrUriChanged: function(model, frbr_uri) {
      if (this.frbr_uri != frbr_uri) {
        this.frbr_uri = frbr_uri;
        this.build();
      }
    },

    checkFrbrUriChange: function(model, new_value) {
      // if the model we're following has changed, rely on the followingFrbrUriChanged instead
      if (this.follow && model == this.follow) return;

      if (new_value == this.frbr_uri || model.previous('frbr_uri') == this.frbr_uri) {
        this.build();
      }
    },

    // An amendment was added. Ensure that all expressions have appropriate amendments.
    amendmentRemoved: function(amendment) {
      // adjust docs who had this expression date, finding a new one
      var oldDate = amendment.get('date'),
          dates = this.amendmentDates(),
          newDate = _.indexOf(dates, oldDate) - 1;

      newDate = (newDate < 0) ? this.initialPublicationDate() : dates[newDate];
      this.each(function(doc) {
        if (doc.get('expression_date') == oldDate) {
          doc.set('expression_date', newDate);
        }
      });

      this.alignAllDocumentAmendments();
    },

    // The date of an amendment changed. Ensure that all expressions linked to that date change, too,
    // and that all documents have the correct amendments.
    amendmentDateChanged: function(model, newDate) {
      var prev = model.previous("date"),
          self = this;

      this.each(function(doc) {
        if (doc.get('expression_date') == prev) {
          doc.set('expression_date', newDate);
        }
      });

      this.alignAllDocumentAmendments();
    },

    alignAllDocumentAmendments: function() {
      var self = this;

      this.each(function(d) {
        self.alignDocumentAmendments(d, {silent: true});
      });

      this.trigger('change');
    },

    // Ensure that all this document has all the appropriate amendments linked to it.
    alignDocumentAmendments: function(doc, options) {
      var date;

      // ensure the document has an expression date
      if (!doc.has('expression_date')) {
        doc.set('expression_date', doc.get('publication_date'));
      }
      date = doc.get('expression_date');

      // apply amendments that are at or before the expression date
      doc.get('amendments').set(this.amendments.filter(function(a) {
        return a.get('date') <= date;
      }));

      if (!options && !options.silent) this.trigger('change');
    },

    initialPublicationDate: function() {
      return this.length === 0 ? null : this.at(0).get('publication_date');
    },

    dates: function() {
      var dates = _.uniq(this.pluck('expression_date'));
      dates.sort();
      return dates;
    },

    amendmentDates: function() {
      var dates = _.uniq(this.amendments.pluck('date'));
      dates.sort();
      return dates;
    },

    // All dates covered by this expression set, including document dates,
    // amendment dates and the initial publication date.
    allDates: function() {
      var dates = this.dates().concat(this.amendmentDates()),
          pubDate = this.initialPublicationDate();

      if (pubDate) dates.push(pubDate);
      dates.sort();
      dates = _.uniq(dates, true);

      return dates;
    },

    atDate: function(date) {
      return this.findWhere({expression_date: date});
    },

    amendmentsAtDate: function(date) {
      return this.amendments.where({date: date});
    },

    // Create a new expression. Returns a deferred that is resolved
    // with the new document document.
    createExpressionAt: function(date) {
      // find the first expression at or before this date, and clone that
      // expression
      var prev = _.last(this.filter(function(d) {
        return d.get('expression_date') <= date;
      }));
      if (!prev) prev = this.at(0);

      var doc = prev.clone();
      var result = $.Deferred();

      doc.set({
        draft: true,
        title: 'Copy of ' + doc.get('title'),
        id: null,
        expression_date: date,
      });

      // ensure it has the necessary amendments linked to it
      this.alignDocumentAmendments(doc, {silent: true});

      if (doc.get('content')) {
        return result.resolve(doc);
      } else {
        // load the content
        var content = new Indigo.DocumentContent({document: prev});
        content.fetch()
          .done(function() {
            doc.set('content', content.get('content'));
            doc.save()
              .then(function() {
                result.resolve(doc);
              })
              .fail(result.fail);
          })
          .fail(result.fail);
      }

      return result;
    },
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
