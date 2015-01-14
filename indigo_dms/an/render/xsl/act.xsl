<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
  xmlns:a="http://www.akomantoso.org/2.0"
  exclude-result-prefixes="a">

  <xsl:import href="elements.xsl" />

  <xsl:output method="html" />

  <xsl:template match="/">
    <xsl:apply-templates select="a:akomaNtoso/a:act" />
  </xsl:template>
  
</xsl:stylesheet> 

