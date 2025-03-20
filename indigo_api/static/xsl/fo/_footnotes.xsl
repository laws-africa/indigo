<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="akn:authorialNote">
    <fo:footnote>
      <fo:inline>
        <xsl:apply-templates select="@marker"/><xsl:text>&#8203;</xsl:text>
      </fo:inline>
      <fo:footnote-body>
        <fo:block-container margin-left="0" margin-top="{$para-spacing}" font-size="{$fontsize-footnote}">
          <!-- don't bold footnotes in headings -->
          <xsl:if test="ancestor::akn:heading">
            <xsl:attribute name="font-weight">normal</xsl:attribute>
          </xsl:if>
          <fo:list-block start-indent="0" provisional-label-separation="{$indent}" text-align="start">
            <fo:list-item>
              <fo:list-item-label end-indent="label-end()">
                <fo:block margin-top="{$para-spacing}" font-size="{$fontsize-small}">
                  <fo:inline baseline-shift="super">
                    <xsl:apply-templates select="@marker"/>
                  </fo:inline>
                </fo:block>
              </fo:list-item-label>
              <fo:list-item-body start-indent="body-start()">
                <fo:block>
                  <!-- don't bold footnotes in headings -->
                  <xsl:if test="ancestor::akn:heading">
                    <xsl:attribute name="font-weight">normal</xsl:attribute>
                  </xsl:if>
                  <xsl:apply-templates/>
                </fo:block>
              </fo:list-item-body>
            </fo:list-item>
          </fo:list-block>
        </fo:block-container>
      </fo:footnote-body>
    </fo:footnote>
  </xsl:template>

</xsl:stylesheet>
