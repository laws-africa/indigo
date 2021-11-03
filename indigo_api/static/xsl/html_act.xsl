<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
  xmlns:a="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
  exclude-result-prefixes="a">

  <xsl:output method="html" />
  <!-- base URL of the resolver for resolving ref elements -->
  <xsl:param name="resolverUrl" />
  <!-- fully-qualified media URL to prepend to relative media urls -->
  <xsl:param name="mediaUrl" />
  <!-- 3-letter language code of document -->
  <xsl:param name="lang" />
  <!-- AKN document type (eg. act) -->
  <xsl:param name="documentType" />
  <!-- AKN document subtype (eg. by-law) -->
  <xsl:param name="subtype" />
  <!-- AKN country code (eg. za) -->
  <xsl:param name="country" />
  <!-- AKN locality code (eg. cpt) -->
  <xsl:param name="locality" />

  <xsl:template match="a:act">
    <xsl:element name="article" namespace="">
      <xsl:attribute name="class">akn-act</xsl:attribute>
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates select="a:coverPage" />
      <xsl:apply-templates select="a:preface" />
      <xsl:apply-templates select="a:preamble" />
      <xsl:apply-templates select="a:body" />
      <xsl:apply-templates select="a:conclusions" />
      <xsl:apply-templates select="a:attachments" />
    </xsl:element>
  </xsl:template>

  <!-- eId attribute is moved to id -->
  <xsl:template match="@eId">
    <xsl:attribute name="id">
      <xsl:value-of select="." />
    </xsl:attribute>
  </xsl:template>

  <!-- copy these attributes directly -->
  <xsl:template match="@colspan | @rowspan | @class | @style">
    <xsl:copy />
  </xsl:template>

  <!-- copy over attributes using a data- prefix, except for 'id' which is prefixed if necessary as-is -->
  <xsl:template match="@*">
    <xsl:variable name="attName" select="concat('data-', local-name(.))"/>
    <xsl:attribute name="{$attName}">
      <xsl:value-of select="." />
    </xsl:attribute>
  </xsl:template>

  <!-- for parts and chapters, include an easily stylable heading -->
  <xsl:template match="a:part">
    <section class="akn-part">
      <xsl:apply-templates select="@*" />
      <h2>
        <xsl:choose>
          <xsl:when test="$lang = 'afr'"><xsl:text>Deel </xsl:text></xsl:when>
          <xsl:when test="$lang = 'ndl'"><xsl:text>Ingcenye </xsl:text></xsl:when>
          <xsl:when test="$lang = 'nso'"><xsl:text>Karolo ya </xsl:text></xsl:when>
          <xsl:when test="$lang = 'sot'"><xsl:text>Karolo </xsl:text></xsl:when>
          <xsl:when test="$lang = 'ssw'"><xsl:text>Incenye </xsl:text></xsl:when>
          <xsl:when test="$lang = 'tsn'"><xsl:text>Karolo </xsl:text></xsl:when>
          <xsl:when test="$lang = 'tso'"><xsl:text>Xiphemu xa </xsl:text></xsl:when>
          <xsl:when test="$lang = 'ven'"><xsl:text>Tshipiḓa tsha </xsl:text></xsl:when>
          <xsl:when test="$lang = 'xho'"><xsl:text>iCandelo </xsl:text></xsl:when>
          <xsl:when test="$lang = 'zul'"><xsl:text>Ingxenye </xsl:text></xsl:when>
          <xsl:otherwise><xsl:text>Part </xsl:text></xsl:otherwise>
        </xsl:choose>
        <xsl:value-of select="a:num" />
        <xsl:choose>
          <xsl:when test="./a:heading">
            <xsl:text> – </xsl:text>
            <xsl:apply-templates select="a:heading" mode="inline" />
          </xsl:when>
        </xsl:choose>
      </h2>
      
      <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
    </section>
  </xsl:template>

  <!-- subpart has no prefix in heading -->
  <xsl:template match="a:subpart">
    <section class="akn-subpart">
      <xsl:apply-templates select="@*" />
      <h2>
        <xsl:if test="a:num">
          <xsl:value-of select="a:num" />
          <xsl:text> – </xsl:text>
        </xsl:if>
        <xsl:apply-templates select="a:heading" mode="inline" />
      </h2>

      <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
    </section>
  </xsl:template>

  <xsl:template match="a:chapter">
    <section class="akn-chapter">
      <xsl:apply-templates select="@*" />
      <h2>
        <xsl:choose>
          <xsl:when test="$lang = 'afr'"><xsl:text>Hoofstuk </xsl:text></xsl:when>
          <xsl:when test="$lang = 'ndl'"><xsl:text>Isahluko </xsl:text></xsl:when>
          <xsl:when test="$lang = 'nso'"><xsl:text>Kgaolo ya </xsl:text></xsl:when>
          <xsl:when test="$lang = 'sot'"><xsl:text>Kgaolo </xsl:text></xsl:when>
          <xsl:when test="$lang = 'ssw'"><xsl:text>Sehluko </xsl:text></xsl:when>
          <xsl:when test="$lang = 'tsn'"><xsl:text>Kgaolo </xsl:text></xsl:when>
          <xsl:when test="$lang = 'tso'"><xsl:text>Kavanyisa ka </xsl:text></xsl:when>
          <xsl:when test="$lang = 'ven'"><xsl:text>Ndima ya </xsl:text></xsl:when>
          <xsl:when test="$lang = 'xho'"><xsl:text>Isahluko </xsl:text></xsl:when>
          <xsl:when test="$lang = 'zul'"><xsl:text>Isahluko </xsl:text></xsl:when>
          <xsl:otherwise><xsl:text>Chapter </xsl:text></xsl:otherwise>
        </xsl:choose>
        <xsl:value-of select="a:num" />
        <br/>
        <xsl:apply-templates select="a:heading" mode="inline" />
      </h2>

      <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
    </section>
  </xsl:template>

  <xsl:template match="a:section">
    <section class="akn-section">
      <xsl:apply-templates select="@*" />
      <h3>
        <xsl:value-of select="a:num" />
        <xsl:text> </xsl:text>
        <xsl:apply-templates select="a:heading" mode="inline" />
      </h3>
      
      <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
    </section>
  </xsl:template>
  
  <xsl:template match="a:subsection">
    <section class="akn-subsection">
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates select="./*[not(self::a:heading)]" />
    </section>
  </xsl:template>

  <!-- crossHeadings - this mimics what the output will be for AKN 3, where crossHeading is a real element -->
  <xsl:template match="a:hcontainer[@name='crossheading']">
    <h3 class="akn-crossHeading">
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates select="a:heading" mode="inline" />
    </h3>
  </xsl:template>
  <!-- don't include name attribute on crossheading output -->
  <xsl:template match="a:hcontainer[@name='crossheading']/@name"/>

  <!-- components/schedules -->
  <xsl:template match="a:attachment">
    <div class="akn-attachment">
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates />
    </div>
  </xsl:template>

  <xsl:template match="a:meta" />

  <xsl:template match="a:attachment/a:heading | a:attachment/a:subheading">
    <h2 class="akn-{local-name()}">
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates />
    </h2>
  </xsl:template>

  <!-- for block elements, generate a span element with a class matching
       the AN name of the node and copy over the attributes -->
  <xsl:template match="a:coverPage | a:preface | a:preamble | a:conclusions">
    <section class="akn-{local-name()}">
      <!-- these components don't have ids in AKN, so add them -->
      <xsl:attribute name="id">
        <xsl:value-of select="local-name()" />
      </xsl:attribute>

      <xsl:apply-templates select="@*" />
      <xsl:apply-templates />
    </section>
  </xsl:template>

  <!-- references -->
  <xsl:template match="a:ref">
    <!-- Create an A element that links to this ref -->
    <a class="akn-ref" data-href="{@href}">
      <xsl:attribute name="href">
        <xsl:choose>
          <xsl:when test="starts-with(@href, '/')">
              <xsl:value-of select="concat($resolverUrl, @href)" />
          </xsl:when>
          <xsl:otherwise>
              <xsl:value-of select="@href" />
          </xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
      <xsl:copy-of select="@*[local-name() != 'href']" />
      <xsl:apply-templates />
    </a>
  </xsl:template>

  <!-- images -->
  <xsl:template match="a:img">
    <img data-src="{@src}">
      <xsl:copy-of select="@*" />

      <!-- make relative image URLs absolute, using the mediaUrl as a base -->
      <xsl:attribute name="src">
        <xsl:choose>
          <xsl:when test="starts-with(@src, 'http://') or starts-with(@src, 'https://')">
            <!-- already absolute -->
            <xsl:value-of select="@src" />
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="concat($mediaUrl, @src)" />
          </xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
    </img>
  </xsl:template>

  <!-- indented elements without numbers should not be indented -->
  <xsl:template match="a:paragraph[not(a:num)] | a:subsection[not(a:num)]">
    <section class="akn-paragraph akn--no-indent">
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates />
    </section>
  </xsl:template>

  <!-- empty p tags must take up space in HTML, so add an nbsp;
       empty means no child elements and only whitespace content -->
  <xsl:template match="a:p[not(*) and not(normalize-space())]">
    <span class="akn-{local-name()}">
      <xsl:apply-templates select="@*" />
      <xsl:text>&#160;</xsl:text>
    </span>
  </xsl:template>

  <!-- for all nodes, generate a SPAN element with a class matching
       the AN name of the node and copy over the attributes -->
  <xsl:template match="*" name="generic-elem">
    <span class="akn-{local-name()}">
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates />
    </span>
  </xsl:template>

  <!-- Special inline mode which doesn't include the akn-foo marker.
       This is used mostly by blocks that format their own headings, and
       don't want akn-heading to be applied to heading elements. -->
  <xsl:template match="*" mode="inline">
    <xsl:apply-templates select="@*" />
    <xsl:apply-templates />
  </xsl:template>
  
  <!-- For HTML table elements, copy them over then apply normal AN
       processing to their contents -->
  <xsl:template match="a:table | a:tr | a:th | a:td">
    <xsl:element name="{local-name()}">
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates />
    </xsl:element>
  </xsl:template>

  <!-- special HTML elements -->
  <xsl:template match="a:a">
    <xsl:element name="a">
      <xsl:copy-of select="@href" />
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates />
    </xsl:element>
  </xsl:template>

  <xsl:template match="a:abbr | a:b | a:i | a:span | a:sub | a:sup | a:u">
    <xsl:element name="{local-name()}">
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates />
    </xsl:element>
  </xsl:template>

  <xsl:template match="a:eol">
    <xsl:element name="br" />
  </xsl:template>

</xsl:stylesheet>
