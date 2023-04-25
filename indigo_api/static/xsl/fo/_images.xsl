<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="akn:img">
    <xsl:choose>
      <xsl:when test="position()=1 and position()=last()">
        <!-- standalone images -->
        <fo:block start-indent="0" text-align="center" margin-top="{$para-spacing}">
          <fo:external-graphic src="{@src}" width="100%"
                               content-height="100%" content-width="scale-to-fit"/>
        </fo:block>
      </xsl:when>
      <xsl:otherwise>
        <!-- inline images -->
        <fo:external-graphic src="{@src}" width="auto"
                             content-height="100%" content-width="scale-to-fit"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
