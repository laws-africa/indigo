<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- headings -->
  <xsl:template match="akn:h1">
    <fo:block font-size="{$fontsize-h1}" margin-top="{$para-spacing}" keep-with-next="always">
      <fo:inline font-weight="bold">
        <xsl:apply-templates/>
      </fo:inline>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:h2">
    <fo:block font-size="{$fontsize-h2}" keep-with-next="always">
      <fo:inline font-weight="bold">
        <xsl:apply-templates/>
      </fo:inline>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:h3">
    <fo:block font-size="{$fontsize-h3}" keep-with-next="always">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:h4">
    <fo:block keep-with-next="always" font-size="{$fontsize-h4}">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <!-- crossheadings -->
  <xsl:template match="akn:crossHeading">
    <fo:block start-indent="0" margin-top="{$para-spacing}*1.5" font-size="{$fontsize-h3}" text-align="center"
              font-weight="bold" font-style="italic">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <!-- p -->
  <xsl:template match="akn:frontMatter//akn:p | akn:preface//akn:p[not(parent::akn:li)] | akn:preamble//akn:p[not(parent::akn:li)] | akn:mainBody/akn:p">
    <fo:block margin-top="{$para-spacing}">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <!-- any p tag in the body if it isn't a first child should be in its own block, e.g.
   - second or third p in a section, paragraph, or quote
   - p in a paragraph after a quote
   -->
  <!-- TODO: Update blockList below to paragraph|subparagraph after Bluebell migration -->
  <xsl:template match="akn:p[position() &gt; 1 or preceding-sibling::akn:blockList] | akn:hcontainer ">
    <fo:block margin-top="{$para-spacing}">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <!-- blockList/listIntroduction goes in a block if it's not the first paragraph -->
  <xsl:template match="akn:listIntroduction">
    <xsl:variable name="parent-position">
      <xsl:value-of select="count(parent::akn:blockList/preceding-sibling::akn:p) + 1"/>
    </xsl:variable>
    <xsl:choose>
      <xsl:when test="$parent-position &gt; 1">
        <fo:block margin-top="{$para-spacing}">
          <xsl:apply-templates/>
        </fo:block>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- wrapUps -->
  <xsl:template match="akn:wrapUp | akn:listWrapUp">
    <fo:block margin-top="{$para-spacing}">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <!-- linebreaks in own block but with no top margin -->
  <xsl:template match="akn:br">
    <fo:block>
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

</xsl:stylesheet>
