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

  <!-- eId attribute is copied to id -->
  <xsl:template match="@eId">
    <xsl:attribute name="id">
      <xsl:value-of select="." />
    </xsl:attribute>
    <xsl:attribute name="data-eId">
      <xsl:value-of select="." />
    </xsl:attribute>
  </xsl:template>

  <!-- copy these attributes directly -->
  <xsl:template match="@colspan | @rowspan | @style | a:img/@alt">
    <xsl:copy />
  </xsl:template>

  <!-- special handling of @class to add both akn-foo and the actual class attribute, if it exists -->
  <xsl:template name="class">
    <xsl:attribute name="class">
      <xsl:value-of select="concat('akn-', local-name())"/>
      <xsl:if test="@class">
        <xsl:value-of select="concat(' ', @class)" />
      </xsl:if>
    </xsl:attribute>
  </xsl:template>

  <xsl:template match="@class" />

  <!-- copy over attributes using a data- prefix, except for 'id' which is prefixed if necessary as-is -->
  <xsl:template match="@*">
    <xsl:variable name="attName" select="concat('data-', local-name(.))"/>
    <xsl:attribute name="{$attName}">
      <xsl:value-of select="." />
    </xsl:attribute>
  </xsl:template>

  <!-- 'hier-heading-' meta template; the different styles determine the content of the h2 -->
  <xsl:template name="hier-heading">
    <xsl:param name="hier-heading-style"/>
    <section>
      <xsl:call-template name="class"/>
      <xsl:apply-templates select="@*" />

      <h2>
        <xsl:choose>
          <xsl:when test="$hier-heading-style='hier-heading-next-line'">
            <xsl:call-template name="hier-heading-next-line"/>
          </xsl:when>
          <xsl:when test="$hier-heading-style='hier-heading-same-line'">
            <xsl:call-template name="hier-heading-same-line"/>
          </xsl:when>
          <xsl:when test="$hier-heading-style='hier-heading-same-line-no-name'">
            <xsl:call-template name="hier-heading-same-line-no-name"/>
          </xsl:when>
        </xsl:choose>
      </h2>

      <xsl:apply-templates select="a:subheading"/>

      <!-- note comes after heading, so not in bold, etc. -->
      <xsl:apply-templates select="a:heading//a:authorialNote | a:subheading//a:authorialNote" mode="content"/>

      <xsl:apply-templates select="./*[not(self::a:num | self::a:heading | self::a:subheading)]" />
    </section>
  </xsl:template>

  <!-- hierarchical elements with h2 headings:
       - name, e.g. 'Chapter', and num on one line
       - heading on the next -->
  <xsl:template name="hier-heading-next-line">
    <xsl:if test="self::a:book">
      <!-- TODO: add translations; use choose (see chapter) -->
      <xsl:text>Book </xsl:text>
    </xsl:if>
    <xsl:if test="self::a:chapter">
      <xsl:choose>
        <xsl:when test="$lang = 'afr'"><xsl:text>Hoofstuk </xsl:text></xsl:when>
        <xsl:when test="$lang = 'cat'"><xsl:text>Capítol </xsl:text></xsl:when>
        <xsl:when test="$lang = 'ell'"><xsl:text>Κeφaλaιo </xsl:text></xsl:when>
        <xsl:when test="$lang = 'fra'"><xsl:text>Chapitre </xsl:text></xsl:when>
        <xsl:when test="$lang = 'kor'">
          <xsl:choose>
            <xsl:when test="a:num">
              <xsl:text>제</xsl:text>
            </xsl:when>
            <xsl:otherwise>
              <xsl:text>장</xsl:text>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:when>
        <xsl:when test="$lang = 'ndl'"><xsl:text>Isahluko </xsl:text></xsl:when>
        <xsl:when test="$lang = 'nso'"><xsl:text>Kgaolo ya </xsl:text></xsl:when>
        <xsl:when test="$lang = 'por'"><xsl:text>Capítulo </xsl:text></xsl:when>
        <xsl:when test="$lang = 'sot'"><xsl:text>Kgaolo </xsl:text></xsl:when>
        <xsl:when test="$lang = 'spa'"><xsl:text>Capitulo </xsl:text></xsl:when>
        <xsl:when test="$lang = 'ssw'"><xsl:text>Sehluko </xsl:text></xsl:when>
        <xsl:when test="$lang = 'swa'">
          <xsl:text>Sura </xsl:text>
          <xsl:if test="a:num">
            <xsl:text>ya </xsl:text>
          </xsl:if>
        </xsl:when>
        <xsl:when test="$lang = 'tsn'"><xsl:text>Kgaolo </xsl:text></xsl:when>
        <xsl:when test="$lang = 'tso'"><xsl:text>Kavanyisa ka </xsl:text></xsl:when>
        <xsl:when test="$lang = 'ven'"><xsl:text>Ndima ya </xsl:text></xsl:when>
        <xsl:when test="$lang = 'xho'"><xsl:text>Isahluko </xsl:text></xsl:when>
        <xsl:when test="$lang = 'zho'"><xsl:text>第</xsl:text></xsl:when>
        <xsl:when test="$lang = 'zul'"><xsl:text>Isahluko </xsl:text></xsl:when>
        <xsl:otherwise><xsl:text>Chapter </xsl:text></xsl:otherwise>
      </xsl:choose>
    </xsl:if>
    <xsl:if test="self::a:title">
      <xsl:choose>
        <xsl:when test="$lang = 'fra'"><xsl:text>Titre </xsl:text></xsl:when>
        <xsl:when test="$lang = 'spa'"><xsl:text>Titulo </xsl:text></xsl:when>
        <xsl:when test="$lang = 'sqi'"><xsl:text>Kreu </xsl:text></xsl:when>
        <xsl:otherwise><xsl:text>Title </xsl:text></xsl:otherwise>
      </xsl:choose>
    </xsl:if>
    <xsl:if test="self::a:tome">
      <!-- TODO: add translations; use choose (see chapter) -->
      <xsl:text>Tome </xsl:text>
    </xsl:if>
    <xsl:value-of select="a:num" />
    <xsl:if test="./a:heading">
      <br/>
    </xsl:if>
    <xsl:apply-templates select="a:heading" mode="inline" />
  </xsl:template>

  <xsl:template match="a:book | a:chapter | a:title | a:tome">
    <xsl:call-template name="hier-heading">
      <xsl:with-param name="hier-heading-style">hier-heading-next-line</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- helper template used in each 'hier-heading-same-line' template -->
  <xsl:template name="optional-dash">
    <!-- the num of the element -->
    <xsl:param name="num"/>
    <!-- final character of num (if there is one) -->
    <xsl:variable name="terminus">
      <xsl:value-of select="substring($num, string-length($num))"/>
    </xsl:variable>
    <xsl:if test="not($terminus='.' or $terminus=':')">
      <xsl:text> –</xsl:text>
    </xsl:if>
    <xsl:text> </xsl:text>
  </xsl:template>

  <!-- hierarchical elements with h2 headings:
       - name, e.g. 'Part'
       - num
       - optional dash, if num doesn't end in "." or ":"
       - heading
       on one line -->
  <xsl:template name="hier-heading-same-line">
    <xsl:if test="self::a:article">
      <xsl:choose>
        <xsl:when test="$lang = 'afr'"><xsl:text>Artikel </xsl:text></xsl:when>
        <xsl:when test="$lang = 'ell'"><xsl:text>Άρθρο </xsl:text></xsl:when>
        <xsl:when test="$lang = 'fra'"><xsl:text>Article </xsl:text></xsl:when>
        <xsl:when test="$lang = 'kor'">
          <xsl:choose>
            <xsl:when test="a:num">
              <xsl:text>제</xsl:text>
            </xsl:when>
            <xsl:otherwise>
              <xsl:text>조</xsl:text>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:when>
        <xsl:when test="$lang = 'por'"><xsl:text>Artigo </xsl:text></xsl:when>
        <xsl:when test="$lang = 'spa'"><xsl:text>Artículo </xsl:text></xsl:when>
        <xsl:when test="$lang = 'sqi'"><xsl:text>Neni </xsl:text></xsl:when>
        <xsl:when test="$lang = 'swa'">
          <xsl:text>Ibara </xsl:text>
          <xsl:if test="a:num">
            <xsl:text>ya </xsl:text>
          </xsl:if>
        </xsl:when>
        <xsl:when test="$lang = 'zho'"><xsl:text>第</xsl:text></xsl:when>
        <xsl:otherwise><xsl:text>Article </xsl:text></xsl:otherwise>
      </xsl:choose>
    </xsl:if>
    <xsl:if test="self::a:clause">
      <!-- TODO: add translations; use choose (see article) -->
      <xsl:text>Clause </xsl:text>
    </xsl:if>
    <xsl:if test="self::a:part">
      <xsl:choose>
        <xsl:when test="$lang = 'afr'"><xsl:text>Deel </xsl:text></xsl:when>
        <xsl:when test="$lang = 'ell'"><xsl:text>Μeρoς </xsl:text></xsl:when>
        <xsl:when test="$lang = 'fra'"><xsl:text>Partie </xsl:text></xsl:when>
        <xsl:when test="$lang = 'ndl'"><xsl:text>Ingcenye </xsl:text></xsl:when>
        <xsl:when test="$lang = 'nso'"><xsl:text>Karolo ya </xsl:text></xsl:when>
        <xsl:when test="$lang = 'por'"><xsl:text>Parte </xsl:text></xsl:when>
        <xsl:when test="$lang = 'sot'"><xsl:text>Karolo </xsl:text></xsl:when>
        <xsl:when test="$lang = 'sqi'"><xsl:text>Pjesa </xsl:text></xsl:when>
        <xsl:when test="$lang = 'ssw'"><xsl:text>Incenye </xsl:text></xsl:when>
        <xsl:when test="$lang = 'swa'">
          <xsl:text>Sehemu </xsl:text>
          <xsl:if test="a:num">
            <xsl:text>ya </xsl:text>
          </xsl:if>
        </xsl:when>
        <xsl:when test="$lang = 'tsn'"><xsl:text>Karolo </xsl:text></xsl:when>
        <xsl:when test="$lang = 'tso'"><xsl:text>Xiphemu xa </xsl:text></xsl:when>
        <xsl:when test="$lang = 'ven'"><xsl:text>Tshipiḓa tsha </xsl:text></xsl:when>
        <xsl:when test="$lang = 'xho'"><xsl:text>iCandelo </xsl:text></xsl:when>
        <xsl:when test="$lang = 'zul'"><xsl:text>Ingxenye </xsl:text></xsl:when>
        <xsl:otherwise><xsl:text>Part </xsl:text></xsl:otherwise>
      </xsl:choose>
    </xsl:if>
    <xsl:value-of select="a:num" />
    <xsl:if test="./a:heading">
      <xsl:call-template name="optional-dash">
        <xsl:with-param name="num" select="a:num"/>
      </xsl:call-template>
    </xsl:if>
    <xsl:apply-templates select="a:heading" mode="inline" />
  </xsl:template>

  <xsl:template match="a:article | a:clause | a:part">
    <xsl:call-template name="hier-heading">
      <xsl:with-param name="hier-heading-style">hier-heading-same-line</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- other hierarchical elements with h2 headings:
       - num
       - optional dash, if num doesn't end in "." or ":"
       - heading
       on one line -->
  <xsl:template name="hier-heading-same-line-no-name">
    <xsl:value-of select="a:num" />
    <xsl:if test="./a:heading and ./a:num">
      <xsl:call-template name="optional-dash">
        <xsl:with-param name="num" select="a:num"/>
      </xsl:call-template>
    </xsl:if>
    <xsl:apply-templates select="a:heading" mode="inline" />
  </xsl:template>

  <xsl:template match="a:division | a:subchapter | a:subclause | a:subdivision | a:subpart | a:subtitle">
    <xsl:call-template name="hier-heading">
      <xsl:with-param name="hier-heading-style">hier-heading-same-line-no-name</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- hierarchical and speech hierarchical (and container) elements with optional num, heading and subheading -->
  <xsl:template match="a:section | a:rule
                       | a:address | a:adjournment | a:administrationOfOath | a:communication | a:debateSection
                       | a:declarationOfVote | a:ministerialStatements | a:nationalInterest | a:noticesOfMotion
                       | a:oralStatements | a:papers | a:personalStatements | a:petitions | a:pointOfOrder | a:prayers
                       | a:proceduralMotions | a:questions | a:resolutions | a:rollCall | a:writtenStatements
                       | a:answer | a:other | a:question | a:speech | a:speechGroup">
    <section>
      <xsl:call-template name="class"/>
      <xsl:apply-templates select="@*" />
      <xsl:if test="a:num or a:heading">
        <h3>
          <xsl:value-of select="a:num" />
          <xsl:choose>
            <xsl:when test="self::a:debateSection">
              <xsl:if test="./a:heading and ./a:num">
                <xsl:text> – </xsl:text>
              </xsl:if>
            </xsl:when>
            <xsl:otherwise>
              <xsl:text> </xsl:text>
            </xsl:otherwise>
          </xsl:choose>
          <xsl:apply-templates select="a:heading" mode="inline" />
        </h3>
      </xsl:if>
      <xsl:apply-templates select="a:subheading"/>

      <!-- note comes after heading, so not in bold, etc. -->
      <xsl:apply-templates select="a:heading//a:authorialNote | a:subheading//a:authorialNote" mode="content"/>

      <xsl:apply-templates select="./*[not(self::a:num | self::a:heading | self::a:subheading)]" />
    </section>
  </xsl:template>

  <!-- generic hierarchical elements are all styled the same -->
  <xsl:template match="a:alinea | a:indent | a:level | a:list | a:paragraph  | a:point | a:proviso | a:sublist | a:subparagraph | a:subrule | a:subsection | a:transitional">
    <section>
      <xsl:call-template name="class"/>
      <!-- indented elements without numbers should not be indented -->
      <xsl:if test="not(a:num)">
        <xsl:attribute name="class"><xsl:value-of select="concat('akn-', local-name(), ' akn--no-indent')"/></xsl:attribute>
      </xsl:if>
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates select="a:num | a:heading | a:subheading"/>
      <xsl:apply-templates select="a:heading//a:authorialNote | a:subheading//a:authorialNote" mode="content"/>
      <xsl:apply-templates select="./*[not(self::a:num | self::a:heading | self::a:subheading)]" />
    </section>
  </xsl:template>

  <xsl:template match="a:crossHeading">
    <h3>
      <xsl:call-template name="class"/>
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates />
    </h3>
    <!-- note comes after heading, so not in bold, etc. -->
    <xsl:apply-templates select=".//a:authorialNote" mode="content"/>
  </xsl:template>

  <xsl:template name="subheading">
    <xsl:call-template name="class"/>
    <xsl:apply-templates select="@*"/>
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="a:subheading">
    <xsl:choose>
      <!-- container subheadings are h3 -->
      <!-- TODO: simplify this? -->
      <xsl:when test="parent::a:article | parent::a:book | parent::a:chapter | parent::a:clause | parent::a:division | parent::a:part | parent::a:subchapter | parent::a:subclause | parent::a:subdivision | parent::a:subpart | parent::a:subtitle | parent::a:title | parent::a:tome">
        <h3>
          <xsl:call-template name="subheading"/>
        </h3>
      </xsl:when>
      <!-- all other subheadings are h4 -->
      <xsl:otherwise>
        <h4>
          <xsl:call-template name="subheading"/>
        </h4>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- block quotes -->
  <xsl:template match="a:embeddedStructure">
    <span>
      <xsl:call-template name="class"/>
      <xsl:apply-templates select="@*"/>
      <!-- opening quote character -->
      <xsl:if test="@startQuote">
        <span class="akn-embeddedStructure--startQuote">
          <xsl:value-of select="@startQuote"/>
        </span>
      </xsl:if>
      <span class="akn-embeddedStructure--content">
        <xsl:apply-templates/>
      </span>
    </span>
  </xsl:template>

  <!-- components/schedules -->
  <xsl:template match="a:attachment">
    <div>
      <xsl:call-template name="class"/>
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates />
    </div>
  </xsl:template>

  <xsl:template match="a:meta" />

  <xsl:template match="a:attachment/a:heading | a:attachment/a:subheading">
    <h2>
      <xsl:call-template name="class"/>
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates />
    </h2>
    <!-- note comes after heading, so not in bold, etc. -->
    <xsl:apply-templates select=".//a:authorialNote" mode="content"/>
  </xsl:template>

  <!-- these components don't have ids in AKN, so add them -->
  <xsl:template match="a:coverPage | a:preface | a:preamble | a:conclusions">
    <section>
      <xsl:call-template name="class"/>
      <xsl:attribute name="id">
        <xsl:value-of select="local-name()" />
      </xsl:attribute>
      <xsl:apply-templates select="@*" />

      <!-- by-laws in ZA get a Preamble heading -->
      <xsl:if test="self::a:preamble and $subtype = 'by-law' and $country = 'za'">
        <h3>
          <xsl:choose>
            <xsl:when test="$lang = 'afr'"><xsl:text>Aanhef</xsl:text></xsl:when>
            <xsl:otherwise><xsl:text>Preamble</xsl:text></xsl:otherwise>
          </xsl:choose>
        </h3>
      </xsl:if>

      <xsl:apply-templates />
    </section>
  </xsl:template>

  <!-- references -->
  <xsl:template match="a:ref">
    <!-- Create an A element that links to this ref -->
    <a data-href="{@href}">
      <xsl:call-template name="class"/>
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
      <xsl:apply-templates select="@*[local-name() != 'href']" />
      <xsl:apply-templates />
    </a>
  </xsl:template>

  <!-- images -->
  <xsl:template match="a:img">
    <img>
      <xsl:call-template name="class"/>
      <xsl:apply-templates select="@*" />

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

  <!-- empty p tags must take up space in HTML, so add an nbsp;
       empty means no child elements and only whitespace content -->
  <xsl:template match="a:p[not(*) and not(normalize-space())]">
    <span>
      <xsl:call-template name="class"/>
      <xsl:apply-templates select="@*" />
      <xsl:text>&#160;</xsl:text>
    </span>
  </xsl:template>

  <!-- authorial notes are made up of two parts:
       1. a reference, inline where the note appears (the default)
       2. the content, as a block element (mode=content)
  -->
  <xsl:template match="a:authorialNote">
    <a>
      <xsl:attribute name="href">
        <xsl:value-of select="concat('#', @eId)" />
      </xsl:attribute>
      <xsl:value-of select="@marker"/>
    </a>
  </xsl:template>

  <xsl:template match="a:authorialNote" mode="content">
    <span>
      <xsl:call-template name="class"/>
      <xsl:apply-templates select="@*" />
      <span class="akn-authorialNote--marker">
        <sup><xsl:value-of select="@marker"/></sup>
      </span>
      <span class="akn-authorialNote--content">
        <xsl:apply-templates />
      </span>
    </span>
  </xsl:template>

  <!-- These are elements that can contain an authorial note.
       This determines at what point the footnote content is shown.
  -->
  <xsl:template match="a:*[self::a:p or self::a:listIntroduction or self::a:listWrapUp][not(ancestor::a:table)][//a:authorialNote]">
    <span>
      <xsl:call-template name="class"/>
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates />

      <xsl:apply-templates select=".//a:authorialNote" mode="content"/>
    </span>
  </xsl:template>

  <!-- for all nodes, generate a SPAN element with a class matching
       the AN name of the node and copy over the attributes -->
  <xsl:template match="*" name="generic-elem">
    <span>
      <xsl:call-template name="class"/>
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
  <xsl:template match="a:table">
    <div class="akn--table-container">
      <table>
        <xsl:call-template name="class"/>
        <xsl:apply-templates select="@*" />
        <xsl:apply-templates />
      </table>

      <!-- footnotes in table cells come after the table -->
      <xsl:apply-templates select=".//a:authorialNote" mode="content"/>
    </div>
  </xsl:template>

  <xsl:template match="a:tr | a:th | a:td">
    <xsl:element name="{local-name()}">
      <xsl:call-template name="class"/>
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates />
    </xsl:element>
  </xsl:template>

  <!-- special HTML elements -->
  <xsl:template match="a:a">
    <a>
      <xsl:call-template name="class"/>
      <xsl:copy-of select="@href" />
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates />
    </a>
  </xsl:template>

  <xsl:template match="a:abbr | a:b | a:i | a:span | a:sub | a:sup | a:u">
    <xsl:element name="{local-name()}">
      <xsl:call-template name="class"/>
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates />
    </xsl:element>
  </xsl:template>

  <xsl:template match="a:eol | a:br">
    <br>
      <xsl:call-template name="class"/>
    </br>
  </xsl:template>

</xsl:stylesheet>
