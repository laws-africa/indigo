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
      this.htmlTransform.setParameter(null, 'mediaUrl', documentModel.url() + '/');
      this.htmlTransform.setParameter(null, 'lang', documentModel.get('language'));
      this.htmlTransform.setParameter(null, 'documentType', documentModel.work.get('nature'));
      this.htmlTransform.setParameter(null, 'subtype', documentModel.get('subtype') || '');
      this.htmlTransform.setParameter(null, 'country', documentModel.work.get('country'));
      this.htmlTransform.setParameter(null, 'locality', documentModel.work.get('locality') || '');
      return this.htmlTransform.transformToFragment(element, document);
    },

    /** Setup for this country, loading the XSL stylesheet, etc.
     *
     * @param document document model
     */
    setup: function(document) {
      var self = this;

      this.document = document;
      this.ready = $.Deferred();

      $.get(document.url() + '/static/xsl/html.xsl').then(function(xml) {
        var htmlTransform = new XSLTProcessor();
        htmlTransform.importStylesheet(xml);
        htmlTransform.setParameter(null, 'resolverUrl', '/works');

        self.htmlTransform = htmlTransform;
        self.ready.resolve();
      });
    },
  };

  Indigo.render.getHtmlRenderer = function(document) {
    var renderer = Object.create(Indigo.render.HtmlRenderer);
    renderer.setup(document);
    return renderer;
  };
});

