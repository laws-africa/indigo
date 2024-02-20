<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template name="heading-keyword">
    <xsl:if test="self::akn:article">
      <xsl:choose>
        <xsl:when test="$language='afr'"><xsl:text>Artikel </xsl:text></xsl:when>
        <xsl:when test="$language='ell'"><xsl:text>Άρθρο </xsl:text></xsl:when>
        <xsl:when test="$language='fra'"><xsl:text>Article </xsl:text></xsl:when>
        <xsl:when test="$language='kor'">
          <xsl:choose>
            <xsl:when test="akn:num">
              <xsl:text>제</xsl:text>
            </xsl:when>
            <xsl:otherwise>
              <xsl:text>조</xsl:text>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:when>
        <xsl:when test="$language='por'"><xsl:text>Artigo </xsl:text></xsl:when>
        <xsl:when test="$language='spa'"><xsl:text>Artículo </xsl:text></xsl:when>
        <xsl:when test="$language='sqi'"><xsl:text>Neni </xsl:text></xsl:when>
        <xsl:when test="$language='swa'">
          <xsl:text>Ibara </xsl:text>
          <xsl:if test="akn:num">
            <xsl:text>ya </xsl:text>
          </xsl:if>
        </xsl:when>
        <xsl:when test="$language='zho'"><xsl:text>第</xsl:text></xsl:when>
        <xsl:otherwise>
          <xsl:text>Article </xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
    <xsl:if test="self::akn:book">
      <xsl:text>Book </xsl:text>
    </xsl:if>
    <xsl:if test="self::akn:clause">
      <xsl:text>Clause </xsl:text>
    </xsl:if>
    <xsl:if test="self::akn:chapter">
      <xsl:choose>
        <xsl:when test="$language='afr'"><xsl:text>Hoofstuk </xsl:text></xsl:when>
        <xsl:when test="$language='cat'"><xsl:text>Capítol </xsl:text></xsl:when>
        <xsl:when test="$language='ell'"><xsl:text>Κeφaλaιo </xsl:text></xsl:when>
        <xsl:when test="$language='fra'"><xsl:text>Chapitre </xsl:text></xsl:when>
        <xsl:when test="$language='kor'">
          <xsl:choose>
            <xsl:when test="akn:num">
              <xsl:text>제</xsl:text>
            </xsl:when>
            <xsl:otherwise>
              <xsl:text>장</xsl:text>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:when>
        <xsl:when test="$language='ndl'"><xsl:text>Isahluko </xsl:text></xsl:when>
        <xsl:when test="$language='nso'"><xsl:text>Kgaolo ya </xsl:text></xsl:when>
        <xsl:when test="$language='por'"><xsl:text>Capítulo </xsl:text></xsl:when>
        <xsl:when test="$language='sot'"><xsl:text>Kgaolo </xsl:text></xsl:when>
        <xsl:when test="$language='spa'"><xsl:text>Capitulo </xsl:text></xsl:when>
        <xsl:when test="$language='ssw'"><xsl:text>Sehluko </xsl:text></xsl:when>
        <xsl:when test="$language='swa'">
          <xsl:text>Sura </xsl:text>
          <xsl:if test="akn:num">
            <xsl:text>ya </xsl:text>
          </xsl:if>
        </xsl:when>
        <xsl:when test="$language='tsn'"><xsl:text>Kgaolo </xsl:text></xsl:when>
        <xsl:when test="$language='tso'"><xsl:text>Kavanyisa ka </xsl:text></xsl:when>
        <xsl:when test="$language='ven'"><xsl:text>Ndima ya </xsl:text></xsl:when>
        <xsl:when test="$language='xho'"><xsl:text>Isahluko </xsl:text></xsl:when>
        <xsl:when test="$language='zho'"><xsl:text>第</xsl:text></xsl:when>
        <xsl:when test="$language='zul'"><xsl:text>Isahluko </xsl:text></xsl:when>
        <xsl:otherwise>
          <xsl:text>Chapter </xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
    <xsl:if test="self::akn:part">
      <xsl:choose>
        <xsl:when test="$language='afr'"><xsl:text>Deel </xsl:text></xsl:when>
        <xsl:when test="$language='deu'"><xsl:text>Abschnitt </xsl:text></xsl:when>
        <xsl:when test="$language='ell'"><xsl:text>Μeρoς </xsl:text></xsl:when>
        <xsl:when test="$language='fra'"><xsl:text>Partie </xsl:text></xsl:when>
        <xsl:when test="$language='ndl'"><xsl:text>Ingcenye </xsl:text></xsl:when>
        <xsl:when test="$language='nso'"><xsl:text>Karolo ya </xsl:text></xsl:when>
        <xsl:when test="$language='por'"><xsl:text>Parte </xsl:text></xsl:when>
        <xsl:when test="$language='sot'"><xsl:text>Karolo </xsl:text></xsl:when>
        <xsl:when test="$language='sqi'"><xsl:text>Pjesa </xsl:text></xsl:when>
        <xsl:when test="$language='ssw'"><xsl:text>Incenye </xsl:text></xsl:when>
        <xsl:when test="$language='swa'">
          <xsl:text>Sehemu </xsl:text>
          <xsl:if test="akn:num">
            <xsl:text>ya </xsl:text>
          </xsl:if>
        </xsl:when>
        <xsl:when test="$language='tsn'"><xsl:text>Karolo </xsl:text></xsl:when>
        <xsl:when test="$language='tso'"><xsl:text>Xiphemu xa </xsl:text></xsl:when>
        <xsl:when test="$language='ven'"><xsl:text>Tshipiḓa tsha </xsl:text></xsl:when>
        <xsl:when test="$language='xho'"><xsl:text>iCandelo </xsl:text></xsl:when>
        <xsl:when test="$language='zul'"><xsl:text>Ingxenye </xsl:text></xsl:when>
        <xsl:otherwise>
          <xsl:text>Part </xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
    <xsl:if test="self::akn:title">
      <xsl:choose>
        <xsl:when test="$language='fra'"><xsl:text>Titre </xsl:text></xsl:when>
        <xsl:when test="$language='spa'"><xsl:text>Título </xsl:text></xsl:when>
        <xsl:when test="$language='sqi'"><xsl:text>Kreu </xsl:text></xsl:when>
        <xsl:otherwise>
          <xsl:text>Title </xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
    <xsl:if test="self::akn:tome">
      <xsl:text>Tome </xsl:text>
    </xsl:if>
  </xsl:template>

  <!-- containers
   - heading centered
   - content
   -->
  <xsl:template name="hier-container">
    <fo:block-container>
      <fo:block margin-top="{$para-spacing}*2" font-size="{$fontsize-h2}" text-align="center" widows="2" orphans="2" keep-with-next="always" id="{@eId}" start-indent="0" font-weight="bold">
        <!-- optionally include startQuote character -->
        <xsl:if test="parent::akn:embeddedStructure and not(preceding-sibling::*)">
          <xsl:call-template name="start-quote">
            <xsl:with-param name="quote-char" select="parent::akn:embeddedStructure/@startQuote"/>
            <!-- num needs to be a nonexistent node, so pass something that'll never exist -->
            <xsl:with-param name="num" select="parent::akn:embeddedStructure/akn:num"/>
          </xsl:call-template>
        </xsl:if>
        <!-- keyword before certain containers -->
        <xsl:call-template name="heading-keyword"/>
        <!-- num is always rendered (if there is one) -->
        <xsl:apply-templates select="akn:num"/>
        <xsl:if test="akn:heading">
          <!-- final character of num (if there is one) -->
          <xsl:variable name="terminus">
            <xsl:value-of select="substring(akn:num, string-length(akn:num))"/>
          </xsl:variable>
          <xsl:choose>
            <!-- certain containers get their heading on the next line -->
            <xsl:when test="self::akn:book or self::akn:chapter or self::akn:title or self::akn:tome">
              <fo:block keep-with-previous="always">
                <xsl:apply-templates select="akn:heading"/>
              </fo:block>
            </xsl:when>
            <!-- certain containers get a dash before the heading, unless there is a num and it ends in a stop or colon -->
            <xsl:when test="self::akn:article or self::akn:clause or self::akn:part">
              <xsl:if test="not($terminus='.' or $terminus=':')">
                <xsl:text> –</xsl:text>
              </xsl:if>
              <xsl:text> </xsl:text>
              <xsl:apply-templates select="akn:heading"/>
            </xsl:when>
            <!-- all other containers get a dash before the heading, only if there is a num and it doesn't end in a stop or colon -->
            <xsl:otherwise>
              <xsl:if test="akn:num and not($terminus='.' or $terminus=':')">
                <xsl:text> –</xsl:text>
              </xsl:if>
              <xsl:text> </xsl:text>
              <xsl:apply-templates select="akn:heading"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:if>
        <xsl:if test="akn:subheading">
          <fo:block font-weight="bold" font-size="{$fontsize-h3}">
            <xsl:apply-templates select="akn:subheading"/>
          </fo:block>
        </xsl:if>
      </fo:block>
      <fo:block margin-top="{$para-spacing}">
        <xsl:apply-templates select="./*[not(self::akn:num|self::akn:heading|self::akn:subheading)]"/>
      </fo:block>
    </fo:block-container>
  </xsl:template>

  <!-- base: use the 'hier container' template for these elements -->
  <xsl:template match="akn:article|akn:book|akn:clause|akn:chapter|akn:division|akn:part|akn:subchapter|akn:subclause|akn:subdivision|akn:subpart|akn:subtitle|akn:title|akn:tome">
    <xsl:call-template name="hier-container"/>
  </xsl:template>

  <!-- schedules
   - heading centered
   - subheading centered
   - content
   -->
  <xsl:template match="akn:attachment">
    <fo:block margin-top="{$para-spacing}*2" font-size="{$fontsize-h2}" text-align="center" widows="2" orphans="2" keep-with-next="always" id="{@eId}">
      <fo:inline font-weight="bold">
        <xsl:apply-templates select="akn:heading"/>
      </fo:inline>
    </fo:block>
    <fo:block margin-top="{$para-spacing}" font-size="{$fontsize-h2}" text-align="center" widows="2" orphans="2" keep-with-next="always">
      <fo:inline font-weight="bold">
        <xsl:apply-templates select="akn:subheading"/>
      </fo:inline>
    </fo:block>
    <xsl:apply-templates select="./*[not(self::akn:heading|self::akn:subheading)]"/>
  </xsl:template>

  <!-- basic unit
   - startQuote if it's the first element in the quote
   - number to the side, bold (if present)
   - heading in bold (if present)
   - subheading in bold (if present)
   - content in next block regardless of whether there's a heading -->
  <xsl:template match="akn:rule|akn:section">
    <!-- use a block container to retain relative indentation (nesting depth) -->
    <fo:block-container>
      <fo:list-block start-indent="0" margin-top="{$para-spacing}*2">
        <fo:list-item id="{@eId}">
          <fo:list-item-label>
            <fo:block font-weight="bold" font-size="{$fontsize-h3}">
              <!-- optionally include startQuote character with num -->
              <xsl:choose>
                <xsl:when test="parent::akn:embeddedStructure and not(preceding-sibling::*) and akn:num">
                  <xsl:call-template name="start-quote">
                    <xsl:with-param name="quote-char" select="parent::akn:embeddedStructure/@startQuote"/>
                    <xsl:with-param name="num" select="akn:num"/>
                  </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="akn:num"/>
                </xsl:otherwise>
              </xsl:choose>
            </fo:block>
          </fo:list-item-label>
          <fo:list-item-body start-indent="{$indent}">
            <!-- basic units always get a heading; use a non-breaking space if it's missing for alignment -->
            <fo:block font-weight="bold" font-size="{$fontsize-h3}" keep-with-next="always">
              <!-- optionally include startQuote character with heading -->
              <xsl:if test="parent::akn:embeddedStructure and not(preceding-sibling::*) and not(akn:num)">
                <xsl:call-template name="start-quote">
                  <xsl:with-param name="quote-char" select="parent::akn:embeddedStructure/@startQuote"/>
                  <xsl:with-param name="num" select="akn:num"/>
                </xsl:call-template>
              </xsl:if>
              <xsl:apply-templates select="akn:heading"/>
              <xsl:if test="not(akn:heading)">
                <xsl:text>&#160;</xsl:text>
              </xsl:if>
            </fo:block>
            <xsl:if test="akn:subheading">
              <fo:block font-weight="bold" font-size="{$fontsize-h4}" keep-with-next="always">
                <xsl:apply-templates select="akn:subheading"/>
              </fo:block>
            </xsl:if>
            <!-- basic unit content always goes below the num -->
            <xsl:apply-templates select="./*[not(self::akn:num|self::akn:heading|self::akn:subheading)]"/>
            <!-- if this element doesn't have content, force an empty block for the heading to keep with next -->
            <xsl:if test="not(./*[not(self::akn:num|self::akn:heading)]//text())">
              <fo:block/>
            </xsl:if>
          </fo:list-item-body>
        </fo:list-item>
      </fo:list-block>
    </fo:block-container>
  </xsl:template>

  <!-- all other hierarchical and numbered elements
   - startQuote if it's the first element in the quote
   - number to the side (if present)
   - heading in bold (if present)
   - subheading in bold (if present)
   - content: either lined up with num or below heading/subheading

   note: using list items means that when a parent element doesn't have content, the nums line up
   e.g. (1) (a) (i) content -->
  <xsl:template match="akn:alinea|akn:indent|akn:blockList/akn:item|akn:level|akn:list|akn:paragraph|akn:point|
                       akn:proviso|akn:sublist|akn:subparagraph|akn:subrule|akn:subsection|akn:transitional|
                       akn:li[not(parent::akn:ul[@class='notice-list'] or parent::akn:ol[@class='amendment-list'])]">
    <!-- use a block container to retain relative indentation (nesting depth) -->
    <fo:block-container>
      <fo:list-block start-indent="0">
        <fo:list-item id="{@eId}">
          <fo:list-item-label>
            <fo:block margin-top="{$para-spacing}">
              <!-- optionally include startQuote character with num -->
              <xsl:choose>
                <xsl:when test="parent::akn:embeddedStructure and not(preceding-sibling::*) and akn:num">
                  <xsl:call-template name="start-quote">
                    <xsl:with-param name="quote-char" select="parent::akn:embeddedStructure/@startQuote"/>
                    <xsl:with-param name="num" select="akn:num"/>
                  </xsl:call-template>
                </xsl:when>
                <xsl:when test="parent::akn:ul/parent::akn:embeddedStructure and not(preceding-sibling::*) and not(parent::akn:ul/preceding-sibling::*)">
                  <xsl:call-template name="start-quote">
                    <xsl:with-param name="quote-char" select="parent::akn:ul/parent::akn:embeddedStructure/@startQuote"/>
                    <xsl:with-param name="num" select="akn:num"/>
                  </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="akn:num"/>
                </xsl:otherwise>
              </xsl:choose>
              <!-- bullets for li -->
              <xsl:if test="self::akn:li">
                <xsl:text>&#x2022;</xsl:text>
              </xsl:if>
            </fo:block>
          </fo:list-item-label>
          <fo:list-item-body start-indent="{$indent}">
            <!-- optional heading in its own block -->
            <xsl:if test="akn:heading">
              <fo:block margin-top="{$para-spacing}" font-weight="bold" keep-with-next="always">
                <!-- optionally include startQuote character with heading -->
                <xsl:if test="parent::akn:embeddedStructure and not(preceding-sibling::*) and not(akn:num)">
                  <xsl:call-template name="start-quote">
                    <xsl:with-param name="quote-char" select="parent::akn:embeddedStructure/@startQuote"/>
                    <xsl:with-param name="num" select="akn:num"/>
                  </xsl:call-template>
                </xsl:if>
                <xsl:apply-templates select="akn:heading"/>
              </fo:block>
            </xsl:if>
            <xsl:if test="akn:subheading">
              <fo:block font-weight="bold" keep-with-next="always">
                <xsl:apply-templates select="akn:subheading"/>
              </fo:block>
            </xsl:if>
            <xsl:apply-templates select="./*[not(self::akn:num|self::akn:heading|self::akn:subheading)]"/>
            <!-- if this element doesn't have content, force an empty block for the heading to keep with next -->
            <xsl:if test="not(./*[not(self::akn:num|self::akn:heading|self::akn:subheading)]//text())">
              <fo:block/>
            </xsl:if>
          </fo:list-item-body>
        </fo:list-item>
      </fo:list-block>
    </fo:block-container>
  </xsl:template>

</xsl:stylesheet>
