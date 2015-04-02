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

      // setup transforms
      $.get('/static/lime/languagesPlugins/akoma3.0/AknToXhtml.xsl')
        .then(function(xml) {
          self.aknToHtml = new XSLTProcessor()
          self.aknToHtml.importStylesheet(xml);
        });
    },

    load: function() {
      if (this.aknToHtml) {
        // TODO: get the raw XML?
        var fragment = this.aknToHtml.transformToFragment(this.model.xmlDocument, document);
        var html = fragment.firstChild.outerHTML;

        var config = {
          docText: html,
          docMarkingLanguage: "akoma3.0",
          docLang: "eng",
        };
        LIME.app.fireEvent("loadDocument", config);
      }
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
