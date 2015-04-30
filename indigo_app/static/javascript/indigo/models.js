(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // The document content could be huge, so the API handles it outside
  // of the document data.
  Indigo.DocumentContent = Backbone.Model.extend({
    url: function() {
      return '/api/documents/' + this.id + '/content';
    },
  });

  // A model-like abstraction for working with
  // document XML in a DOM form
  Indigo.DocumentDom = Backbone.Model.extend({
    setXml: function(xml, options) {
      try {
        this.xmlDocument = $.parseXML(xml);
      } catch(e) {
        Indigo.errorView.show("The document has invalid XML.");
      }
      this.trigger('change', options);
    },

    // serialise an XML node, or the entire document if node is not given, to a string
    toXml: function(node) {
      return new XMLSerializer().serializeToString(node || this.xmlDocument);
    },

    updateFragment: function(oldNode, newNode) {
      if (!oldNode || !oldNode.parentNode) {
        // entire document has changed
        console.log('Replacing whole document');
        this.xmlDocument = newNode;
      } else {
        // just a fragment has changed
        console.log('Replacing node');
        newNode = oldNode.ownerDocument.importNode(newNode, true);
        oldNode.parentNode.replaceChild(newNode, oldNode);
      }

      this.trigger('change');

      return newNode;
    },
  });

  Indigo.Document = Backbone.Model.extend({
    defaults: {
      draft: true,
      title: '(none)',
    },
  });

  Indigo.Library = Backbone.Collection.extend({
    model: Indigo.Document,
    url: '/api/documents'
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
})(window);
