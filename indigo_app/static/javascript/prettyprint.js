(function(exports) {
  var xsltSource =
    '<?xml version="1.0"?>' +
    '<!-- template to pretty-print XML -->' +
    '<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">' +
    '  <xsl:output method="xml" indent="yes"/>' +
    '  <xsl:strip-space elements="*"/>' +
    '' +
    '  <xsl:template match="node() | @*">' +
    '    <xsl:copy>' +
    '      <xsl:apply-templates select="node() | @*" />' +
    '    </xsl:copy>' +
    '  </xsl:template>' +
    '' +
    '</xsl:stylesheet>';

  var serializer = new XMLSerializer();
  var transform = new XSLTProcessor();
  transform.importStylesheet($.parseXML(xsltSource));

  exports.prettyPrintXml = function(xml) {
    if (typeof(xml) == "string") {
      // squash whitespace
      xml = $.parseXML(xml.replace(/([\n\r]| +)/g, ' '));
    }
    xml = transform.transformToDocument(xml);
    return serializer.serializeToString(xml);
  };
})(window);
