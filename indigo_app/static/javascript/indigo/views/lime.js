(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // Handle the document editor, tracking changes and saving it back to the server.
  // The model is an Indigo.DocumentContent instance.
  Indigo.LimeEditorView = Backbone.View.extend({
    el: '#lime-tab',
    events: {
      'click .save-lime-btn': 'save',
      'click .load-lime-btn': 'load',
    },

    initialize: function(options) {
      var self = this;
    },

    load: function() {
      // TODO: get the raw XML from the raw model?
      LIME.XsltTransforms.transform(
        this.model.xmlDocument, '/static/lime/languagesPlugins/akoma3.0/AknToXhtml.xsl', {},
        function(html) {
          var config = {
            docText: html.firstChild.outerHTML,
            docMarkingLanguage: "akoma3.0",
            docLang: "eng",
          };
          LIME.app.fireEvent("loadDocument", config);
        });
    },

    save: function() {
      var self = this;

      console.log('Fetching XML from LIME');
      LIME.app.fireEvent("translateRequest", function(xml) {
        self.model.updateFragment(null, xml);
      }, {
        serialize: false,
      });
    },
  });
})(window);
