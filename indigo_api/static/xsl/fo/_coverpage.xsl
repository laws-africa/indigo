<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="akn:div[@class='coverpage']">
    <fo:block text-align="center">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:div[@class='place-name']|akn:div[@class='parent-work']">
    <fo:block>
      <xsl:if test="@class='place-name'">
        <xsl:attribute name="font-size"><xsl:value-of select="$fontsize-h1"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="@class='parent-work'">
        <xsl:attribute name="font-size"><xsl:value-of select="$fontsize-h2"/></xsl:attribute>
        <xsl:attribute name="margin-top"><xsl:value-of select="$para-spacing"/></xsl:attribute>
      </xsl:if>
      <fo:inline font-weight="bold">
        <xsl:apply-templates/>
      </fo:inline>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:ul[@class='notice-list']">
    <fo:block margin-top="{$para-spacing}">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="akn:ol[@class='amendment-list']">
    <fo:block margin-top="{$para-spacing}*2">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <!-- notice list items -->
  <xsl:template match="akn:ul[@class='notice-list']/akn:li|akn:ol[@class='amendment-list']/akn:li">
    <fo:block margin-top="{$para-spacing}">
      <xsl:if test="@class='commencement-note' or @class='amendment'">
        <xsl:attribute name="margin-top">0</xsl:attribute>
      </xsl:if>
      <xsl:choose>
        <!-- assent date and commencement date are bold -->
        <xsl:when test="@class='assent-date' or @class='commencement-date'">
          <fo:inline font-weight="bold">
            <xsl:apply-templates/>
          </fo:inline>
        </xsl:when>
        <!-- notes, notices, amendments and repeals are italics -->
        <xsl:when test="@class='commencement-note' or @class='as-at-date-notice' or @class='verification-notice' or @class='amendment' or @class='amendment repeal'">
          <fo:inline font-style="italic">
            <xsl:apply-templates/>
          </fo:inline>
        </xsl:when>
        <!-- publication-info -->
        <xsl:otherwise>
          <xsl:apply-templates/>
        </xsl:otherwise>
      </xsl:choose>
    </fo:block>
  </xsl:template>

</xsl:stylesheet>
