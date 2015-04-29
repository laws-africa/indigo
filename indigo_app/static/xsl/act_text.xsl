<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
  xmlns:a="http://www.akomantoso.org/2.0"
  exclude-result-prefixes="a">

  <xsl:output method="text" indent="no" omit-xml-declaration="yes" />
  <xsl:strip-space elements="*"/>

  <xsl:template match="a:act">
    <xsl:apply-templates select="a:coverPage" />
    <xsl:apply-templates select="a:preface" />
    <xsl:apply-templates select="a:preamble" />
    <xsl:apply-templates select="a:body" />
    <xsl:apply-templates select="a:conclusions" />
  </xsl:template>

  <xsl:template match="a:preamble">
    <xsl:text>PREAMBLE</xsl:text>
    <xsl:text>

</xsl:text>
    <xsl:apply-templates />
  </xsl:template>

  <xsl:template match="a:part">
    <xsl:text>Part </xsl:text>
    <xsl:value-of select="./a:num" />
    <xsl:text> - </xsl:text>
    <xsl:value-of select="./a:heading" />
    <xsl:text>

</xsl:text>
    <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
  </xsl:template>

  <xsl:template match="a:chapter">
    <xsl:text>Chapter </xsl:text>
    <xsl:value-of select="./a:num" />
    <xsl:text>
</xsl:text>
    <xsl:value-of select="./a:heading" />
    <xsl:text>

</xsl:text>
    <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
  </xsl:template>

  <xsl:template match="a:section">
    <xsl:value-of select="a:num" />
    <xsl:text> </xsl:text>
    <xsl:if test="a:heading != ''">
      <xsl:value-of select="a:heading" />
    </xsl:if>
    <xsl:text>

</xsl:text>
    <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
    <xsl:text>
</xsl:text>
  </xsl:template>
  
  <xsl:template match="a:subsection">
    <xsl:if test="a:num != ''">
      <xsl:value-of select="a:num" />
      <xsl:text> </xsl:text>
    </xsl:if>
    <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
    <xsl:text>

</xsl:text>
  </xsl:template>

  <xsl:template match="a:blockList">
    <xsl:if test="a:listIntroduction != ''">
      <xsl:value-of select="a:listIntroduction" />
      <xsl:text>

</xsl:text>
    </xsl:if>
    <xsl:apply-templates select="./*[not(self::a:listIntroduction)]" />
  </xsl:template>

  <xsl:template match="a:item">
    <xsl:value-of select="./a:num" />
    <xsl:text> </xsl:text>
    <xsl:apply-templates select="./*[not(self::a:num)]" />
    <xsl:text>

</xsl:text>
  </xsl:template>

  <xsl:template match="a:list">
    <xsl:if test="a:intro != ''">
      <xsl:value-of select="a:intro" />
      <xsl:text>

</xsl:text>
    </xsl:if>
    <xsl:apply-templates select="./*[not(self::a:intro)]" />
  </xsl:template>


  <!-- components/schedules -->
  <xsl:template match="a:doc">
    <xsl:if test="a:meta/a:identification/a:FRBRWork/a:FRBRalias">
      <xsl:value-of select="a:meta/a:identification/a:FRBRWork/a:FRBRalias/@value" />
      <xsl:text>

</xsl:text>
    </xsl:if>

    <xsl:apply-templates select="a:coverPage" />
    <xsl:apply-templates select="a:preface" />
    <xsl:apply-templates select="a:preamble" />
    <xsl:apply-templates select="a:mainBody" />
    <xsl:apply-templates select="a:conclusions" />
  </xsl:template>

  <!-- for all nodes, generate a SPAN element with a class matching
       the AN name of the node and copy over the ID if it exists -->
  <xsl:template match="*">
    <xsl:text/><xsl:apply-templates /><xsl:text/>
  </xsl:template>
  
</xsl:stylesheet>
