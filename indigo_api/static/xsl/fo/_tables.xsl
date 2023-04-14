<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="akn:table">
    <fo:table width="100%" table-layout="fixed"
              margin-top="{$para-spacing-table}" margin-bottom="{$para-spacing-table}"
              keep-together="1">
      <fo:table-body>
        <xsl:apply-templates/>
      </fo:table-body>
    </fo:table>
  </xsl:template>

  <xsl:template match="akn:tr">
    <fo:table-row>
      <xsl:apply-templates/>
    </fo:table-row>
  </xsl:template>

  <xsl:template match="akn:th | akn:td">
    <fo:table-cell border-style="solid" border-color="{$table-border-colour}" padding="6pt">
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
        </xsl:if>
        <xsl:apply-templates/>
      </fo:block>
    </fo:table-cell>
  </xsl:template>

</xsl:stylesheet>
