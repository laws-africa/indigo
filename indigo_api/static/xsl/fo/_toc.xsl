<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- table of contents -->
  <xsl:template match="akn:toc">
    <!-- outdent the first level -->
    <fo:block margin-top="{$para-spacing}" start-indent="-{$indent-toc}">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:div[@name='toc-level']">
    <fo:block-container>
      <fo:block start-indent="{$indent-toc}">
        <xsl:apply-templates/>
      </fo:block>
    </fo:block-container>
  </xsl:template>

  <xsl:template match="akn:tocItem">
    <fo:block margin-top="{$para-spacing}" text-align-last="justify">
      <fo:inline>
        <fo:basic-link internal-destination="{@id}">
          <xsl:apply-templates/>
          <xsl:text> </xsl:text><fo:leader leader-pattern="dots"/><xsl:text> </xsl:text>
          <fo:page-number-citation ref-id="{@id}"/>
        </fo:basic-link>
      </fo:inline>
    </fo:block>
  </xsl:template>

  <!-- bookmarks -->
  <xsl:template match="akn:div[@name='toc-level']" mode="bookmarks">
    <xsl:call-template name="bookmark-item">
      <xsl:with-param name="ref-id" select="akn:tocItem/@id"/>
      <xsl:with-param name="ref-title" select="akn:tocItem/text()"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="bookmark-item">
    <xsl:param name="ref-id"/>
    <xsl:param name="ref-title"/>
    <fo:bookmark internal-destination="{$ref-id}">
      <fo:bookmark-title>
        <xsl:value-of select="$ref-title"/>
      </fo:bookmark-title>
      <xsl:apply-templates select="akn:div[@name='toc-level']" mode="bookmarks"/>
    </fo:bookmark>
  </xsl:template>

</xsl:stylesheet>
