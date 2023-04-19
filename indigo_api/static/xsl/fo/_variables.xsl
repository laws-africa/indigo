<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:variable name="font-fam">PT Serif</xsl:variable>
  <xsl:variable name="font-fam-frontmatter">PT Sans</xsl:variable>
  <xsl:variable name="font-fam-headings">PT Sans</xsl:variable>
  <xsl:variable name="fontsize">9pt</xsl:variable>
  <!-- 15.3pt -->
  <xsl:variable name="fontsize-h1">
    <xsl:value-of select="$fontsize"/> * 1.7
  </xsl:variable>
  <!-- 11.25pt -->
  <xsl:variable name="fontsize-h2">
    <xsl:value-of select="$fontsize"/> * 1.25
  </xsl:variable>
  <!-- 10.26pt -->
  <xsl:variable name="fontsize-h3">
    <xsl:value-of select="$fontsize"/> * 1.14
  </xsl:variable>
  <!-- 9pt -->
  <xsl:variable name="fontsize-h4" select="$fontsize"/>
  <!-- 7.2pt -->
  <xsl:variable name="fontsize-footnote">
    <xsl:value-of select="$fontsize"/> * 0.8
  </xsl:variable>
  <!-- 11.25pt -->
  <xsl:variable name="fontsize-frontmatter" select="$fontsize-h2"/>
  <!-- 9pt -->
  <xsl:variable name="fontsize-frontmatter-small" select="$fontsize"/>
  <!-- 6pt -->
  <xsl:variable name="fontsize-small">
    <xsl:value-of select="$fontsize"/> * 0.66
  </xsl:variable>
  <!-- 10pt -->
  <xsl:variable name="para-spacing">0.8em</xsl:variable>
  <xsl:variable name="para-spacing-quote">
    <xsl:value-of select="$para-spacing"/> * 1.5
  </xsl:variable>
  <xsl:variable name="para-spacing-table">
    <xsl:value-of select="$para-spacing"/> * 2
  </xsl:variable>
  <xsl:variable name="indent-int">3</xsl:variable>
  <xsl:variable name="indent">3em</xsl:variable>
  <xsl:variable name="indent-quote">2em</xsl:variable>
  <xsl:variable name="indent-bullets">1.5em</xsl:variable>
  <xsl:variable name="indent-toc">1.5em</xsl:variable>
  <xsl:variable name="link-colour">#D04242</xsl:variable>
  <xsl:variable name="link-colour-internal">#3E1313</xsl:variable>
  <xsl:variable name="accent-colour">#D04242</xsl:variable>
  <xsl:variable name="white">#FFFFFF</xsl:variable>
  <xsl:variable name="warning-colour">#7C2727</xsl:variable>
  <xsl:variable name="table-border-colour">#DDDDDD</xsl:variable>

</xsl:stylesheet>
