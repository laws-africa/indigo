<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="html" encoding="utf-8" />

  <!-- ignore these elements -->
  <xsl:template match="head|style|script|link" />

  <!-- remove these elements -->
  <xsl:template match="div[not(starts-with(@id, 'sdfootnote'))] | span | font">
    <xsl:apply-templates />
  </xsl:template>

  <!-- strong to b -->
  <xsl:template match="strong">
    <b><xsl:apply-templates /></b>
  </xsl:template>

  <!-- em to i -->
  <xsl:template match="em">
    <i><xsl:apply-templates /></i>
  </xsl:template>

  <!-- headings to bold text -->
  <xsl:template match="h1 | h2 | h3 | h4 | h5">
    <p><b><xsl:apply-templates /></b></p>
  </xsl:template>

  <!-- for most nodes, just copy -->
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
