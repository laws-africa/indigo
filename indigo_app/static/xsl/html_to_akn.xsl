<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
  xmlns:html="http://www.w3.org/1999/xhtml"
  xmlns="http://www.akomantoso.org/2.0"
  exclude-result-prefixes="html">

  <xsl:output method="xml" />

  <!-- tables -->

  <xsl:template match="html:table">
    <table>
      <xsl:apply-templates select="@id | //html:tr" />
    </table>
  </xsl:template>

  <xsl:template match="html:tr">
    <tr>
      <xsl:apply-templates select="node()" />
    </tr>
  </xsl:template>

  <xsl:template match="html:td | html:th">
		<xsl:element name="{name(.)}">
      <xsl:apply-templates select="@colspan | @rowspan" />

      <p>
        <xsl:for-each select="node()">
          <xsl:choose>
            <xsl:when test="name(.) = 'p'">
              <!-- ignore p (we already have one) and do children -->
              <xsl:apply-templates select="node()"/>
            </xsl:when>

            <xsl:otherwise>
              <xsl:apply-templates select="."/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:for-each>
      </p>

    </xsl:element>
  </xsl:template>

  <!-- elements -->

  <xsl:template match="html:p">
    <p>
      <xsl:apply-templates />
    </p>
  </xsl:template>

  <xsl:template match="html:br">
    <eol/>
  </xsl:template>

  <!-- attributes -->

  <xsl:template match="@id | @colspan | @rowspan">
    <xsl:attribute name="{name(.)}"><xsl:value-of select="." /></xsl:attribute>
  </xsl:template>

  <!-- text -->

  <xsl:template match="text()">
    <xsl:value-of select="normalize-space(.)"/>
  </xsl:template>

</xsl:stylesheet>
