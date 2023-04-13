<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="akn:preface|akn:preamble">
    <fo:block margin-top="{$para-spacing}*2">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:preface/akn:p">
    <fo:block margin-top="{$para-spacing}">
      <!-- optional styling of 'ACT' in the preface -->
      <xsl:if test="text()='ACT'">
        <xsl:attribute name="text-align">center</xsl:attribute>
        <xsl:attribute name="keep-with-next">always</xsl:attribute>
        <xsl:attribute name="font-size"><xsl:value-of select="$fontsize-h1"/></xsl:attribute>
        <xsl:attribute name="font-weight">bold</xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:longTitle">
    <fo:inline font-weight="bold">
      <xsl:apply-templates/>
    </fo:inline>
  </xsl:template>

</xsl:stylesheet>
