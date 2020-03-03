$(function() {
  if (!Indigo.render) Indigo.render = {};

  Indigo.render.HtmlRenderer = {
    /* A Deferred object that can be waited upon to ensure that the renderer has loaded
       its XSL transform and is ready to render.
     */
    ready: null,

    /** Renders an XML element from a document into HTML.
     *
     * @param documentModel Document model instance
     * @param element xml element
     * @returns {DocumentFragment}
     */
    renderXmlElement: function(documentModel, element) {
      this.htmlTransform.setParameter(null, 'defaultIdScope', this.getElementIdScope(element) || '');
      this.htmlTransform.setParameter(null, 'mediaUrl', documentModel.url() + '/');
      this.htmlTransform.setParameter(null, 'lang', documentModel.get('language'));
      this.htmlTransform.setParameter(null, 'documentType', documentModel.work.get('nature'));
      this.htmlTransform.setParameter(null, 'subtype', documentModel.get('subtype') || '');
      this.htmlTransform.setParameter(null, 'country', documentModel.work.get('country'));
      this.htmlTransform.setParameter(null, 'locality', documentModel.work.get('locality') || '');
      return this.htmlTransform.transformToFragment(element, document);
    },

    /** Default scope for ID attribute of rendered elements.
     */
    getElementIdScope: function(element) {
      var ns = element.namespaceURI;
      var idScope = element.ownerDocument.evaluate(
        "./ancestor::a:doc[@name][1]/@name",
        element,
        function(x) { if (x == "a") return ns; },
        XPathResult.ANY_TYPE,
        null);

      idScope = idScope.iterateNext();
      return idScope ? idScope.value : null;
    },

    /** Setup for this country, loading the XSL stylesheet, etc.
     *
     * @param country country code
     */
    setup: function(country) {
      var self = this;

      this.country = country;
      this.ready = $.Deferred();

      function loaded(xml) {
        var htmlTransform = new XSLTProcessor();
        htmlTransform.importStylesheet(xml);
        htmlTransform.setParameter(null, 'resolverUrl', '/works');

        self.htmlTransform = htmlTransform;
        self.ready.resolve();
      }

      $.get('/static/xsl/act-' + country +'.xsl')
        .then(loaded)
        .fail(function() {
          $.get('/static/xsl/act.xsl')
            .then(loaded);
        });
    },
  };

  // Map from country codes to initialized renderers
  Indigo.render.htmlRenderers = {};

  Indigo.render.getHtmlRenderer = function(country) {
    if (!Indigo.render.htmlRenderers[country]) {
      var renderer = Indigo.render.htmlRenderers[country] = Object.create(Indigo.render.HtmlRenderer);
      renderer.setup(country);
    }

    return Indigo.render.htmlRenderers[country];
  };
});

