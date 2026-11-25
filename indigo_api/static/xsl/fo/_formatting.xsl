<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <!-- Explicit text utilities applied by document authors. Fixed tiers do not compound on nesting. -->
  <xsl:template name="formatting-attributes">
    <xsl:param name="inherit-alignment" select="false()"/>
    <xsl:variable name="classes" select="concat(' ', normalize-space(@class), ' ')"/>
    <xsl:choose>
      <xsl:when test="contains($classes, ' akn--text-xxsmall ')"><xsl:attribute name="font-size">6pt</xsl:attribute></xsl:when>
      <xsl:when test="contains($classes, ' akn--text-xsmall ')"><xsl:attribute name="font-size">7pt</xsl:attribute></xsl:when>
      <xsl:when test="contains($classes, ' akn--text-small ')"><xsl:attribute name="font-size">8pt</xsl:attribute></xsl:when>
      <xsl:when test="contains($classes, ' akn--text-normal ')"><xsl:attribute name="font-size"><xsl:value-of select="$fontsize"/></xsl:attribute></xsl:when>
    </xsl:choose>
    <xsl:variable name="alignment" select="ancestor-or-self::*[
      ($inherit-alignment or generate-id()=generate-id(current())) and (
      contains(concat(' ', normalize-space(@class), ' '), ' akn--text-left ') or
      contains(concat(' ', normalize-space(@class), ' '), ' akn--text-center ') or
      contains(concat(' ', normalize-space(@class), ' '), ' akn--text-right ') or
      contains(concat(' ', normalize-space(@class), ' '), ' akn--text-justify ') or
      @style='left' or @style='center' or @style='right' or @style='justify')][1]"/>
    <xsl:for-each select="$alignment">
      <xsl:variable name="tokens" select="concat(' ', normalize-space(@class), ' ')"/>
      <xsl:attribute name="text-align"><xsl:choose>
        <xsl:when test="contains($tokens, ' akn--text-justify ')">justify</xsl:when>
        <xsl:when test="contains($tokens, ' akn--text-right ')">end</xsl:when>
        <xsl:when test="contains($tokens, ' akn--text-center ')">center</xsl:when>
        <xsl:when test="contains($tokens, ' akn--text-left ')">start</xsl:when>
        <xsl:when test="@style='right'">end</xsl:when>
        <xsl:when test="@style='left'">start</xsl:when>
        <xsl:otherwise><xsl:value-of select="@style"/></xsl:otherwise>
      </xsl:choose></xsl:attribute>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="table-padding-attributes">
    <xsl:if test="ancestor-or-self::*[(self::akn:table or self::akn:td or self::akn:th) and contains(concat(' ', normalize-space(@class), ' '), ' akn--no-padding ')]">
      <xsl:attribute name="padding-top">0pt</xsl:attribute>
      <xsl:attribute name="padding-bottom">0pt</xsl:attribute>
      <xsl:attribute name="padding-left">0pt</xsl:attribute>
      <xsl:attribute name="padding-right">0pt</xsl:attribute>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>
