(function(exports) {
  var xsltSource =
    '<?xml version="1.0"?>' +
    '<!--' +
    '  Pretty-print Akoma Ntoso XML. Indents only nodes that cannot contain significant whitespace.' +
    '  Derived from https://www.xml.com/pub/a/2006/11/29/xslt-xml-pretty-printer.html' +
    '-->' +
    '' +
    '<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"' +
    '  xmlns:a="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">' +
    '  ' +
    '  <xsl:output method="xml" indent="no" encoding="UTF-8"/>' +
    '  <xsl:strip-space elements="*"/>' +
    '  <xsl:preserve-space elements="a:a a:affectedDocument a:b a:block a:caption a:change a:concept a:courtType a:date a:def a:del a:docCommittee a:docDate a:docIntroducer a:docJurisdiction a:docNumber a:docProponent a:docPurpose a:docStage a:docStatus a:docTitle a:docType a:docketNumber a:entity a:event a:extractText a:fillIn a:from a:heading a:i a:inline a:ins a:judge a:lawyer a:legislature a:li a:listConclusion a:listIntroduction a:location a:mmod a:mod a:mref a:narrative a:neutralCitation a:num a:object a:omissis a:opinion a:organization a:outcome a:p a:party a:person a:placeholder a:process a:quantity a:quotedText a:recordedTime a:ref a:relatedDocument a:remark a:rmod a:role a:rref a:scene a:session a:shortTitle a:signature a:span a:sub a:subheading a:summary a:sup a:term a:tocItem a:u a:vote"/>' +
    '' +
    '  <!-- dont indent children of these elements -->' +
    '  <xsl:template match="a:a|a:affectedDocument|a:b|a:block|a:caption|a:change|a:concept|a:courtType|a:date|a:def|a:del|a:docCommittee|a:docDate|a:docIntroducer|a:docJurisdiction|a:docNumber|a:docProponent|a:docPurpose|a:docStage|a:docStatus|a:docTitle|a:docType|a:docketNumber|a:entity|a:event|a:extractText|a:fillIn|a:from|a:heading|a:i|a:inline|a:ins|a:judge|a:lawyer|a:legislature|a:li|a:listConclusion|a:listIntroduction|a:location|a:mmod|a:mod|a:mref|a:narrative|a:neutralCitation|a:num|a:object|a:omissis|a:opinion|a:organization|a:outcome|a:p|a:party|a:person|a:placeholder|a:process|a:quantity|a:quotedText|a:recordedTime|a:ref|a:relatedDocument|a:remark|a:rmod|a:role|a:rref|a:scene|a:session|a:shortTitle|a:signature|a:span|a:sub|a:subheading|a:summary|a:sup|a:term|a:tocItem|a:u|a:vote">' +
    '    <xsl:param name="depth">0</xsl:param>' +
    '' +
    '    <xsl:text>&#xA;</xsl:text>' +
    '    <xsl:call-template name="indent">' +
    '      <xsl:with-param name="depth" select="$depth"/>' +
    '    </xsl:call-template>' +
    '' +
    '    <xsl:copy-of select="." />' +
    '  </xsl:template>' +
    '' +
    '  <!-- Indent children of these elements -->' +
    '  <xsl:template match="*|comment()">' +
    '    <xsl:param name="depth">0</xsl:param>' +
    '' +
    '    <xsl:if test="$depth &gt; 0">' +
    '      <xsl:text>&#xA;</xsl:text>' +
    '    </xsl:if>' +
    '' +
    '    <xsl:call-template name="indent">' +
    '      <xsl:with-param name="depth" select="$depth"/>' +
    '    </xsl:call-template>' +
    '' +
    '    <xsl:copy>' +
    '      <xsl:if test="self::*">' +
    '        <xsl:copy-of select="@*"/>' +
    '' +
    '        <xsl:apply-templates>' +
    '          <xsl:with-param name="depth" select="$depth + 1"/>' +
    '        </xsl:apply-templates>' +
    '' +
    '        <xsl:if test="count(*) &gt; 0">' +
    '          <xsl:text>&#xA;</xsl:text>' +
    '' +
    '          <xsl:call-template name="indent">' +
    '            <xsl:with-param name="depth" select="$depth"/>' +
    '          </xsl:call-template>' +
    '        </xsl:if>' +
    '      </xsl:if>' +
    '    </xsl:copy>' +
    '' +
    '    <xsl:variable name="isLastNode" select="count(../..) = 0 and position() = last()"/>' +
    '    <xsl:if test="$isLastNode">' +
    '      <xsl:text>&#xA;</xsl:text>' +
    '    </xsl:if>' +
    '  </xsl:template>' +
    '' +
    '  <xsl:template name="indent">' +
    '    <xsl:param name="depth"/>' +
    '' +
    '    <xsl:if test="$depth &gt; 0">' +
    '      <xsl:text>  </xsl:text>' +
    '' +
    '      <xsl:call-template name="indent">' +
    '        <xsl:with-param name="depth" select="$depth - 1"/>' +
    '      </xsl:call-template>' +
    '    </xsl:if>' +
    '  </xsl:template>' +
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
