<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- quotes are indented from both sides relative to their parent -->
  <!-- TODO: test and adjust once quotes are supported -->
  <xsl:template match="akn:embeddedStructure">
    <fo:block-container margin-top="{$para-spacing-quote}" margin-bottom="{$para-spacing-quote}" keep-with-previous="always">
      <fo:block start-indent="{$indent-quote}" end-indent="{$indent-quote}">
        <!-- don't include opening quote here if the quote doesn't start with a p -->
        <xsl:if test="akn:p">
          <xsl:call-template name="start-quote">
            <xsl:with-param name="quote-char" select="@startQuote"/>
          </xsl:call-template>
        </xsl:if>
        <xsl:apply-templates/>
      </fo:block>
    </fo:block-container>
  </xsl:template>

  <!-- outdent the opening quote so that the blocks in the quote line up visually -->
  <xsl:template name="start-quote">
    <xsl:param name="quote-char"/>
    <fo:inline-container width="0" margin-left="-{string-length($quote-char)}*6pt">
      <fo:block>
        <xsl:apply-templates select="$quote-char"/>
      </fo:block>
    </fo:inline-container>
  </xsl:template>

</xsl:stylesheet>
