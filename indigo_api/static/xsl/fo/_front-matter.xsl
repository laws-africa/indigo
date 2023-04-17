<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="akn:frontMatter">
    <!-- TODO: background image (different on first page) -->
    <fo:block font-family="{$font-fam-frontmatter}" font-size="{$fontsize-frontmatter-small}">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:container">
    <fo:block page-break-after="always">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <!-- TODO: make this less brittle, will be overridden per place and h4 won't always be there, might need more than 10% for right-aligned multiple logos, or there might be none, etc. -->
  <xsl:template match="akn:div[@name='first-page-header']">
    <fo:block border-bottom-style="solid" border-bottom-color="{$accent-colour}">
      <fo:inline-container width="90%">
        <xsl:apply-templates select="akn:h4"/>
      </fo:inline-container>
      <fo:inline-container width="10%">
        <fo:block>
          <xsl:apply-templates select="akn:img"/>
        </fo:block>
      </fo:inline-container>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:div[@name='place']">
    <fo:block margin-top="{$para-spacing}*3" font-size="{$fontsize-frontmatter}">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:div[@name='parent-work-title']">
    <fo:block font-size="{$fontsize-frontmatter}">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:div[@name='short-title']">
    <fo:block margin-top="{$para-spacing}*2" font-size="{$fontsize-h1}">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:div[@name='numbered-title']">
    <fo:block font-size="{$fontsize-frontmatter}">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:div[@name='expression-detail']">
    <fo:block margin-top="{$para-spacing}*2">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:div[@name='updates-block']">
    <fo:block margin-top="{$para-spacing}*4">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:div[@name='about']">
    <fo:block margin-top="{$para-spacing}*4">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:div[@name='licence']">
    <fo:block margin-top="{$para-spacing}*4">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:div">
    <fo:block margin-top="{$para-spacing}">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

</xsl:stylesheet>
