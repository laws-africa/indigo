<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="akn:table">
    <fo:table width="100%" table-layout="fixed"
              margin-top="{$para-spacing-table}" margin-bottom="{$para-spacing-table}">
      <xsl:if test="@class='border'">
        <xsl:attribute name="border"><xsl:value-of select="$table-border-outer"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates select="akn:colgroup"/>
      <xsl:if test="akn:tr[@style='header-row']">
        <fo:table-header>
          <xsl:apply-templates select="akn:tr[@style='header-row']"/>
        </fo:table-header>
      </xsl:if>
      <fo:table-body>
        <xsl:apply-templates select="*[not(self::akn:colgroup or self::akn:tr[@style='header-row'])]"/>
      </fo:table-body>
    </fo:table>
  </xsl:template>

  <xsl:template match="akn:col">
    <fo:table-column column-width="{@width}">
      <xsl:if test="ancestor::akn:table[@class='border'] and not(position()=last())">
        <xsl:attribute name="border-right"><xsl:value-of select="$table-border-inner"/></xsl:attribute>
      </xsl:if>
    </fo:table-column>
  </xsl:template>

  <xsl:template match="akn:tr">
    <fo:table-row>
      <xsl:if test="ancestor::akn:table[@class='border'] and not(position()=last())">
        <xsl:attribute name="border-bottom"><xsl:value-of select="$table-border-inner"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="ancestor::akn:table[@class='border'] and @style='header-row'">
        <xsl:attribute name="border-bottom"><xsl:value-of select="$table-border-outer"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </fo:table-row>
  </xsl:template>

  <xsl:template match="akn:th | akn:td">
    <fo:table-cell padding="6pt" keep-together.within-column="always" min-height="1em">
      <xsl:if test="@colspan">
        <xsl:attribute name="number-columns-spanned"><xsl:value-of select="@colspan"/></xsl:attribute>
      </xsl:if>
      <xsl:if test="@rowspan">
        <xsl:attribute name="number-rows-spanned"><xsl:value-of select="@rowspan"/></xsl:attribute>
      </xsl:if>
      <fo:block start-indent="0" text-align="start" font-weight="normal">
        <!-- headings are bold and centered -->
        <xsl:if test="self::akn:th">
          <xsl:attribute name="font-weight">bold</xsl:attribute>
          <xsl:attribute name="text-align">center</xsl:attribute>
          <xsl:attribute name="keep-with-next">1</xsl:attribute>
        </xsl:if>
        <!-- honour alignment -->
        <xsl:if test="@style='right'">
          <xsl:attribute name="text-align">end</xsl:attribute>
        </xsl:if>
        <xsl:if test="@style='center'">
          <xsl:attribute name="text-align">center</xsl:attribute>
        </xsl:if>
        <xsl:apply-templates/>
      </fo:block>
    </fo:table-cell>
  </xsl:template>

</xsl:stylesheet>
