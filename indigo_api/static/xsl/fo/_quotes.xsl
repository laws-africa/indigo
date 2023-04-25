<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- quotes are indented from both sides relative to their parent -->
  <xsl:template match="akn:embeddedStructure">
    <fo:block-container margin-top="{$para-spacing-quote}" margin-bottom="{$para-spacing-quote}" keep-with-previous="always">
      <fo:block start-indent="{$indent-quote}" end-indent="{$indent-quote}">
        <xsl:apply-templates/>
      </fo:block>
    </fo:block-container>
  </xsl:template>

  <!-- include the opening quote before the first p, if the quote starts with a p -->
  <!-- otherwise it'll get included before the first num -->
  <xsl:template match="akn:embeddedStructure/akn:p">
    <fo:block margin-top="{$para-spacing-quote}">
      <xsl:if test="position()=1">
        <xsl:call-template name="start-quote">
          <xsl:with-param name="quote-char" select="parent::akn:embeddedStructure/@startQuote"/>
          <xsl:with-param name="num" select="akn:num"/>
        </xsl:call-template>
      </xsl:if>
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <!-- outdent the opening quote so that the blocks in the quote line up visually -->
  <xsl:template name="start-quote">
    <xsl:param name="quote-char"/>
    <xsl:param name="num"/>
    <fo:inline-container width="0" margin-left="-{string-length($quote-char)}*4pt">
      <fo:block margin-top="-{$para-spacing}">
        <xsl:apply-templates select="$quote-char"/>
        <xsl:apply-templates select="$num"/>
      </fo:block>
    </fo:inline-container>
  </xsl:template>

</xsl:stylesheet>
