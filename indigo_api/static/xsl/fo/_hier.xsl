<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- containers
   - heading centered
   - content
   -->
  <xsl:template match="akn:article|akn:chapter|akn:division|akn:part|akn:subdivision|akn:subpart">
    <fo:block-container>
      <fo:block margin-top="{$para-spacing}*2" font-size="{$fontsize-h2}" text-align="center" widows="2" orphans="2" keep-with-next="always" id="{@eId}" start-indent="0">
        <fo:inline font-weight="bold">
          <xsl:choose>
            <xsl:when test="self::akn:chapter">
              <xsl:text>Chapter </xsl:text>
            </xsl:when>
            <xsl:when test="self::akn:part">
              <xsl:text>Part </xsl:text>
            </xsl:when>
          </xsl:choose>
          <xsl:apply-templates select="akn:num"/>
          <!-- only include dash / break before the heading if there is a heading -->
          <xsl:if test="akn:heading">
            <xsl:choose>
              <xsl:when test="self::akn:chapter or self::akn:article">
                <fo:block>
                  <xsl:apply-templates select="akn:heading"/>
                </fo:block>
              </xsl:when>
              <xsl:when test="self::akn:part">
                <xsl:text> – </xsl:text>
                <xsl:apply-templates select="akn:heading"/>
              </xsl:when>
              <!-- don't include dash in subpart if there is no num (because it has no prefix) -->
              <xsl:otherwise>
                <xsl:if test="akn:num">
                  <xsl:text> – </xsl:text>
                </xsl:if>
                <xsl:apply-templates select="akn:heading"/>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:if>
        </fo:inline>
      </fo:block>
      <fo:block margin-top="{$para-spacing}">
        <xsl:apply-templates select="./*[not(self::akn:num|self::akn:heading)]"/>
      </fo:block>
    </fo:block-container>
  </xsl:template>

</xsl:stylesheet>
