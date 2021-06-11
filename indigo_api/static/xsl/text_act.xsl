<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
  xmlns:a="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
  exclude-result-prefixes="a">

  <xsl:output method="text" indent="no" omit-xml-declaration="yes" />

  <!-- strip whitespace from most elements, but preserve whitespace in inline elements that can contain text -->
  <xsl:strip-space elements="*"/>
  <xsl:preserve-space elements="a:a a:affectedDocument a:b a:block a:caption a:change a:concept a:courtType a:date a:def a:del a:docCommittee a:docDate a:docIntroducer a:docJurisdiction a:docNumber a:docProponent a:docPurpose a:docStage a:docStatus a:docTitle a:docType a:docketNumber a:entity a:event a:extractText a:fillIn a:from a:heading a:i a:inline a:ins a:judge a:lawyer a:legislature a:li a:listConclusion a:listIntroduction a:location a:mmod a:mod a:mref a:narrative a:neutralCitation a:num a:object a:omissis a:opinion a:organization a:outcome a:p a:party a:person a:placeholder a:process a:quantity a:quotedText a:recordedTime a:ref a:relatedDocument a:remark a:rmod a:role a:rref a:scene a:session a:shortTitle a:signature a:span a:sub a:subheading a:summary a:sup a:term a:tocItem a:u a:vote"/>

  <!-- replaces "value" in "text" with "replacement" -->
  <xsl:template name="string-replace-all">
    <xsl:param name="text" />
    <xsl:param name="value" />
    <xsl:param name="replacement" />

    <xsl:choose>
      <xsl:when test="$text = '' or $value = '' or not($value)">
        <xsl:value-of select="$text" />
      </xsl:when>
      <xsl:when test="contains($text, $value)">
        <xsl:value-of select="substring-before($text, $value)"/>
        <xsl:value-of select="$replacement" />
        <xsl:call-template name="string-replace-all">
          <xsl:with-param name="text" select="substring-after($text, $value)" />
          <xsl:with-param name="value" select="$value" />
          <xsl:with-param name="replacement" select="$replacement" />
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$text" />
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- Escape inline markers with a backslash -->
  <xsl:template name="escape-inlines">
    <xsl:param name="text" />

    <!-- This works from the inside out, first escaping backslash chars themselves, then escaping
          the different types of inline markers -->
    <xsl:call-template name="string-replace-all">
      <xsl:with-param name="text">
        <xsl:call-template name="string-replace-all">
          <xsl:with-param name="text">
            <xsl:call-template name="string-replace-all">
              <xsl:with-param name="text">
                <xsl:call-template name="string-replace-all">
                  <xsl:with-param name="text">
                    <xsl:call-template name="string-replace-all">
                      <xsl:with-param name="text">
                        <xsl:call-template name="string-replace-all">
                          <xsl:with-param name="text">
                            <xsl:call-template name="string-replace-all">
                              <xsl:with-param name="text">
                                <xsl:call-template name="string-replace-all">
                                  <xsl:with-param name="text">
                                    <xsl:call-template name="string-replace-all">
                                      <xsl:with-param name="text">
                                        <xsl:call-template name="string-replace-all">
                                          <xsl:with-param name="text">
                                            <xsl:call-template name="string-replace-all">
                                              <xsl:with-param name="text" select="$text" />
                                              <xsl:with-param name="value"><xsl:value-of select="'\'" /></xsl:with-param>
                                              <xsl:with-param name="replacement"><xsl:value-of select="'\\'" /></xsl:with-param>
                                            </xsl:call-template>
                                          </xsl:with-param>
                                          <xsl:with-param name="value"><xsl:value-of select="'**'" /></xsl:with-param>
                                          <xsl:with-param name="replacement"><xsl:value-of select="'\*\*'" /></xsl:with-param>
                                        </xsl:call-template>
                                      </xsl:with-param>
                                      <xsl:with-param name="value"><xsl:value-of select="'__'" /></xsl:with-param>
                                      <xsl:with-param name="replacement"><xsl:value-of select="'\_\_'" /></xsl:with-param>
                                    </xsl:call-template>
                                  </xsl:with-param>
                                  <xsl:with-param name="value"><xsl:value-of select="'//'" /></xsl:with-param>
                                  <xsl:with-param name="replacement"><xsl:value-of select="'\/\/'" /></xsl:with-param>
                                </xsl:call-template>
                              </xsl:with-param>
                              <xsl:with-param name="value"><xsl:value-of select="'_^'" /></xsl:with-param>
                              <xsl:with-param name="replacement"><xsl:value-of select="'\_^'" /></xsl:with-param>
                            </xsl:call-template>
                          </xsl:with-param>
                          <xsl:with-param name="value"><xsl:value-of select="'^_'" /></xsl:with-param>
                          <xsl:with-param name="replacement"><xsl:value-of select="'\^_'" /></xsl:with-param>
                        </xsl:call-template>
                      </xsl:with-param>
                      <xsl:with-param name="value"><xsl:value-of select="'^^'" /></xsl:with-param>
                      <xsl:with-param name="replacement"><xsl:value-of select="'\^\^'" /></xsl:with-param>
                  </xsl:call-template>
                </xsl:with-param>
                <xsl:with-param name="value"><xsl:value-of select="'!['" /></xsl:with-param>
                <xsl:with-param name="replacement"><xsl:value-of select="'\!['" /></xsl:with-param>
              </xsl:call-template>
              </xsl:with-param>
              <xsl:with-param name="value"><xsl:value-of select="']('" /></xsl:with-param>
              <xsl:with-param name="replacement"><xsl:value-of select="'\]('" /></xsl:with-param>
            </xsl:call-template>
          </xsl:with-param>
          <xsl:with-param name="value"><xsl:value-of select="'[['" /></xsl:with-param>
          <xsl:with-param name="replacement"><xsl:value-of select="'\[\['" /></xsl:with-param>
        </xsl:call-template>
      </xsl:with-param>
      <xsl:with-param name="value"><xsl:value-of select="']]'" /></xsl:with-param>
      <xsl:with-param name="replacement"><xsl:value-of select="'\]\]'" /></xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- adds a backslash to the start of the value param, if necessary -->
  <xsl:template name="escape-prefixes">
    <xsl:param name="value"/>

    <xsl:variable name="prefix" select="translate(substring($value, 1, 13), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')" />
    <!-- '(' is considered special, so translate numbers into '(' so we can find and escape them -->
    <xsl:variable name="numprefix" select="translate(substring($value, 1, 3), '1234567890', '((((((((((')" />

    <xsl:variable name="slash">
      <!-- p tags must escape initial content that looks like a block element marker -->
      <xsl:if test="$prefix = 'BODY' or
                    $prefix = 'PREAMBLE' or
                    $prefix = 'PREFACE' or
                    starts-with($prefix, 'CHAPTER ') or
                    starts-with($prefix, 'PART ') or
                    starts-with($prefix, 'SUBPART ') or
                    starts-with($prefix, 'SCHEDULE ') or
                    starts-with($prefix, 'HEADING ') or
                    starts-with($prefix, 'SUBHEADING ') or
                    starts-with($prefix, 'LONGTITLE ') or
                    starts-with($prefix, 'CROSSHEADING ') or
                    starts-with($prefix, '{|') or
                    starts-with($numprefix, '(')">
        <xsl:value-of select="'\'" />
      </xsl:if>
    </xsl:variable>

    <xsl:value-of select="concat($slash, $value)" />
  </xsl:template>

  <!-- adds a backslash to the start of the text param, if necessary -->
  <xsl:template name="escape">
    <xsl:param name="value"/>

    <xsl:variable name="escaped">
      <xsl:call-template name="escape-inlines">
        <xsl:with-param name="text" select="$value" />
      </xsl:call-template>
    </xsl:variable>

    <xsl:call-template name="escape-prefixes">
      <xsl:with-param name="value" select="$escaped" />
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="a:act">
    <xsl:apply-templates select="a:coverPage" />
    <xsl:apply-templates select="a:preface" />
    <xsl:apply-templates select="a:preamble" />
    <xsl:apply-templates select="a:body" />
    <xsl:apply-templates select="a:conclusions" />
    <xsl:apply-templates select="a:attachments/a:attachment" />
  </xsl:template>

  <xsl:template match="a:preface">
    <xsl:text>PREFACE</xsl:text>
    <xsl:text>&#10;&#10;</xsl:text>

    <xsl:apply-templates />
  </xsl:template>

  <xsl:template match="a:preamble">
    <xsl:text>PREAMBLE</xsl:text>
    <xsl:text>&#10;&#10;</xsl:text>

    <xsl:apply-templates />
  </xsl:template>

  <xsl:template match="a:body">
    <xsl:text>BODY</xsl:text>
    <xsl:text>&#10;&#10;</xsl:text>

    <xsl:apply-templates />
  </xsl:template>

  <xsl:template match="a:part">
    <xsl:text>Part </xsl:text>
    <xsl:value-of select="a:num" />
    <xsl:text> - </xsl:text>
    <xsl:apply-templates select="a:heading" />
    <xsl:text>&#10;&#10;</xsl:text>

    <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
  </xsl:template>

  <xsl:template match="a:subpart">
    <xsl:text>Subpart </xsl:text>
    <xsl:value-of select="a:num" />
    <xsl:text> - </xsl:text>
    <xsl:apply-templates select="a:heading" />
    <xsl:text>&#10;&#10;</xsl:text>

    <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
  </xsl:template>

  <xsl:template match="a:chapter">
    <xsl:text>Chapter </xsl:text>
    <xsl:value-of select="a:num" />
    <xsl:text> - </xsl:text>
    <xsl:apply-templates select="a:heading" />
    <xsl:text>&#10;&#10;</xsl:text>

    <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
  </xsl:template>

  <xsl:template match="a:section">
    <xsl:value-of select="a:num" />
    <xsl:text> </xsl:text>
    <xsl:apply-templates select="a:heading" />
    <xsl:text>&#10;&#10;</xsl:text>

    <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
  </xsl:template>
  
  <xsl:template match="a:subsection">
    <xsl:if test="a:num != ''">
      <xsl:value-of select="a:num" />
      <xsl:text> </xsl:text>
    </xsl:if>

    <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
  </xsl:template>

  <!-- crossheadings -->
  <xsl:template match="a:hcontainer[@name='crossheading']">
    <xsl:text>CROSSHEADING </xsl:text>
    <xsl:apply-templates select="a:heading" />
    <xsl:text>&#10;&#10;</xsl:text>
  </xsl:template>

  <!-- longtitle -->
  <xsl:template match="a:longTitle">
    <xsl:text>LONGTITLE </xsl:text>
    <xsl:apply-templates />
    <xsl:text>&#10;&#10;</xsl:text>
  </xsl:template>

  <!-- p tags must end with a blank line -->
  <xsl:template match="a:p">
    <xsl:apply-templates/>
    <xsl:text>&#10;&#10;</xsl:text>
  </xsl:template>

  <xsl:template match="a:blockList">
    <xsl:if test="a:listIntroduction != ''">
      <xsl:apply-templates select="a:listIntroduction" />
      <xsl:text>&#10;&#10;</xsl:text>
    </xsl:if>
    <xsl:apply-templates select="./*[not(self::a:listIntroduction)]" />
  </xsl:template>

  <xsl:template match="a:item">
    <xsl:value-of select="a:num" />
    <xsl:text> </xsl:text>
    <xsl:apply-templates select="./*[not(self::a:num)]" />
  </xsl:template>

  <xsl:template match="a:list">
    <xsl:if test="a:intro != ''">
      <xsl:apply-templates select="a:intro" />
      <xsl:text>&#10;&#10;</xsl:text>
    </xsl:if>
    <xsl:apply-templates select="./*[not(self::a:intro)]" />
  </xsl:template>

  <!-- first text nodes of these elems must be escaped if they have special chars -->
  <xsl:template match="a:p[not(ancestor::a:table)]/text()[not(preceding-sibling::*)] | a:listIntroduction/text()[not(preceding-sibling::*)] | a:intro/text()[not(preceding-sibling::*)]">
    <xsl:call-template name="escape">
      <xsl:with-param name="value" select="." />
    </xsl:call-template>
  </xsl:template>

  <!-- escape inlines in text nodes -->
  <xsl:template match="text()">
    <xsl:call-template name="escape-inlines">
      <xsl:with-param name="text" select="." />
    </xsl:call-template>
  </xsl:template>


  <!-- attachments/schedules -->
  <xsl:template match="a:attachment">
    <xsl:text>SCHEDULE&#10;HEADING </xsl:text>
    <xsl:apply-templates select="a:heading" />
    <xsl:text>&#10;</xsl:text>

    <xsl:if test="a:subheading">
      <xsl:text>SUBHEADING </xsl:text>
      <xsl:apply-templates select="a:subheading" />
      <xsl:text>&#10;</xsl:text>
    </xsl:if>

    <xsl:text>&#10;</xsl:text>
    <xsl:apply-templates select="a:doc/a:mainBody" />
  </xsl:template>


  <!-- tables -->
  <xsl:template match="a:table">
    <xsl:text>{| </xsl:text>

    <!-- attributes -->
    <xsl:for-each select="@*[local-name()!='eId']">
      <xsl:value-of select="local-name(.)" />
      <xsl:text>="</xsl:text>
      <xsl:value-of select="." />
      <xsl:text>" </xsl:text>
    </xsl:for-each>
    <xsl:text>&#10;|-</xsl:text>

    <xsl:apply-templates />
    <xsl:text>&#10;|}&#10;&#10;</xsl:text>
  </xsl:template>

  <xsl:template match="a:tr">
    <xsl:apply-templates />
    <xsl:text>&#10;|-</xsl:text>
  </xsl:template>

  <xsl:template match="a:th|a:td">
    <xsl:choose>
      <xsl:when test="local-name(.) = 'th'">
        <xsl:text>&#10;! </xsl:text>
      </xsl:when>
      <xsl:when test="local-name(.) = 'td'">
        <xsl:text>&#10;| </xsl:text>
      </xsl:when>
    </xsl:choose>

    <!-- attributes -->
    <xsl:if test="@*">
      <xsl:for-each select="@*">
        <xsl:value-of select="local-name(.)" />
        <xsl:text>="</xsl:text>
        <xsl:value-of select="." />
        <xsl:text>" </xsl:text>
      </xsl:for-each>
      <xsl:text>| </xsl:text>
    </xsl:if>

    <xsl:apply-templates />
  </xsl:template>

  <!-- don't end p tags with newlines in tables -->
  <xsl:template match="a:table//a:p">
    <xsl:apply-templates />
  </xsl:template>

  <!-- END tables -->

  <xsl:template match="a:remark">
    <xsl:text>[</xsl:text>
    <xsl:apply-templates />
    <xsl:text>]</xsl:text>
  </xsl:template>

  <xsl:template match="a:ref">
    <xsl:text>[</xsl:text>
    <xsl:apply-templates />
    <xsl:text>](</xsl:text>
    <xsl:value-of select="@href" />
    <xsl:text>)</xsl:text>
  </xsl:template>

  <xsl:template match="a:img">
    <xsl:text>![</xsl:text>
    <xsl:value-of select="@alt" />
    <xsl:text>](</xsl:text>
    <xsl:value-of select="@src" />
    <xsl:text>)</xsl:text>
  </xsl:template>

  <xsl:template match="a:i">
    <xsl:text>//</xsl:text>
    <xsl:apply-templates />
    <xsl:text>//</xsl:text>
  </xsl:template>

  <xsl:template match="a:b">
    <xsl:text>**</xsl:text>
    <xsl:apply-templates />
    <xsl:text>**</xsl:text>
  </xsl:template>

  <xsl:template match="a:sup">
    <xsl:text>^^</xsl:text>
    <xsl:apply-templates />
    <xsl:text>^^</xsl:text>
  </xsl:template>

  <xsl:template match="a:sub">
    <xsl:text>_^</xsl:text>
    <xsl:apply-templates />
    <xsl:text>^_</xsl:text>
  </xsl:template>

  <xsl:template match="a:u">
    <xsl:text>__</xsl:text>
    <xsl:apply-templates />
    <xsl:text>__</xsl:text>
  </xsl:template>

  <xsl:template match="a:eol">
    <xsl:text>&#10;</xsl:text>
  </xsl:template>


  <!-- for most nodes, just dump their text content -->
  <xsl:template match="*">
    <xsl:apply-templates />
  </xsl:template>
  
</xsl:stylesheet>
