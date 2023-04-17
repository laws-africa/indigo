<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="akn:b">
    <fo:inline font-weight="bold">
      <xsl:apply-templates/>
    </fo:inline>
  </xsl:template>

  <xsl:template match="akn:i">
    <fo:inline font-style="italic">
      <xsl:apply-templates/>
    </fo:inline>
  </xsl:template>

  <xsl:template match="akn:u">
    <fo:inline text-decoration="underline">
      <xsl:apply-templates/>
    </fo:inline>
  </xsl:template>

  <xsl:template match="akn:sup">
    <fo:inline baseline-shift="super" font-size="{$fontsize-small}">
      <xsl:apply-templates/>
    </fo:inline>
  </xsl:template>

  <xsl:template match="akn:sub">
    <fo:inline baseline-shift="sub" font-size="{$fontsize-small}">
      <xsl:apply-templates/>
    </fo:inline>
  </xsl:template>

  <!-- defined terms -->
  <xsl:template match="akn:def">
    <fo:inline font-weight="bold">
      <xsl:apply-templates/>
    </fo:inline>
  </xsl:template>

  <!-- annotations (editorial remarks) -->
  <xsl:template match="akn:remark[@status='editorial']">
    <xsl:choose>
      <!-- when it's the only child, treat it as a block -->
      <xsl:when test="position()=1 and position()=last()">
        <fo:block keep-with-previous="always" font-style="italic">
          <xsl:apply-templates/>
        </fo:block>
      </xsl:when>
      <!-- otherwise, treat it as an inline -->
      <xsl:otherwise>
        <fo:inline font-style="italic">
          <xsl:apply-templates/>
        </fo:inline>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- links (only if href isn't empty) -->
  <xsl:template match="akn:a[@href!='' and not(parent::akn:div[@name='update-button'])]|akn:ref[@href!='']">
    <xsl:choose>
      <xsl:when test="starts-with(@href, '#')">
        <fo:basic-link internal-destination="{substring-after(@href, '#')}" color="{$link-colour-internal}" text-decoration="underline">
          <xsl:apply-templates/>
        </fo:basic-link>
      </xsl:when>
      <xsl:otherwise>
        <fo:basic-link external-destination="{@href}" color="{$link-colour}" text-decoration="underline">
          <xsl:apply-templates/>
        </fo:basic-link>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
