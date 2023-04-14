<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- TODO: test and adjust once footnotes are supported -->
  <xsl:template match="akn:authorialNote">
    <fo:footnote>
      <fo:inline>
        <xsl:apply-templates select="@marker"/>
      </fo:inline>
      <fo:footnote-body>
        <fo:block-container margin="0">
          <fo:block margin-top="{$para-spacing}" font-size="{$fontsize-footnote}">
            <fo:inline-container width="0" margin-left="-{$indent}"
                                 baseline-shift="super" font-size="{$fontsize-small}">
              <fo:block>
                <xsl:apply-templates select="@marker"/>
              </fo:block>
            </fo:inline-container>
            <xsl:apply-templates/>
          </fo:block>
        </fo:block-container>
      </fo:footnote-body>
    </fo:footnote>
  </xsl:template>

</xsl:stylesheet>
