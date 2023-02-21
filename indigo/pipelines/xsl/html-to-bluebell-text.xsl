<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns="http://www.w3.org/1999/xhtml">

  <xsl:output method="text" indent="no" omit-xml-declaration="yes" encoding="utf-8" />
  <!-- strip whitespace from most elements, but preserve whitespace in inline elements that can contain text -->
  <xsl:strip-space elements="*"/>
  <xsl:preserve-space elements="em a"/>

  <!-- helpers -->
  <!-- trims whitespace from the left of a string -->
  <xsl:template name="string-ltrim">
    <xsl:param name="text" />
    <xsl:param name="trim" select="'&#09;&#10;&#13; '" />

    <xsl:if test="string-length($text) &gt; 0">
      <xsl:choose>
        <xsl:when test="contains($trim, substring($text, 1, 1))">
          <xsl:call-template name="string-ltrim">
            <xsl:with-param name="text" select="substring($text, 2)" />
            <xsl:with-param name="trim" select="$trim" />
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$text" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
  </xsl:template>

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
                          <!-- replace newlines with spaces -->
                          <xsl:with-param name="text" select="translate($text, '&#13;&#10;', '  ')" />
                          <xsl:with-param name="value"><xsl:value-of select="'\'" /></xsl:with-param>
                          <xsl:with-param name="replacement"><xsl:value-of select="'\\'" /></xsl:with-param>
                        </xsl:call-template>
                      </xsl:with-param>
                      <xsl:with-param name="value"><xsl:value-of select="'**'" /></xsl:with-param>
                      <xsl:with-param name="replacement"><xsl:value-of select="'\*\*'" /></xsl:with-param>
                    </xsl:call-template>
                  </xsl:with-param>
                  <xsl:with-param name="value"><xsl:value-of select="'//'" /></xsl:with-param>
                  <xsl:with-param name="replacement"><xsl:value-of select="'\/\/'" /></xsl:with-param>
                </xsl:call-template>
              </xsl:with-param>
              <xsl:with-param name="value"><xsl:value-of select="'__'" /></xsl:with-param>
              <xsl:with-param name="replacement"><xsl:value-of select="'\_\_'" /></xsl:with-param>
            </xsl:call-template>
          </xsl:with-param>
          <xsl:with-param name="value"><xsl:value-of select="'{{'" /></xsl:with-param>
          <xsl:with-param name="replacement"><xsl:value-of select="'\{\{'" /></xsl:with-param>
        </xsl:call-template>
      </xsl:with-param>
      <xsl:with-param name="value"><xsl:value-of select="'}}'" /></xsl:with-param>
      <xsl:with-param name="replacement"><xsl:value-of select="'\}\}'" /></xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- Escape prefixes with a backslash -->
  <xsl:template name="escape-prefixes">
    <xsl:param name="text" />

    <xsl:variable name="slash">
      <!-- p tags must escape initial content that looks like a block element marker -->
      <xsl:if test="$text = 'ARGUMENTS' or
                    $text = 'BACKGROUND' or
                    $text = 'BODY' or
                    $text = 'CONCLUSIONS' or
                    $text = 'DECISION' or
                    $text = 'INTRODUCTION' or
                    $text = 'MOTIVATION' or
                    $text = 'PREAMBLE' or
                    $text = 'PREFACE' or
                    $text = 'REMEDIES' or
                    starts-with($text, 'ALINEA') or
                    starts-with($text, 'ANNEXURE') or
                    starts-with($text, 'APPENDIX') or
                    starts-with($text, 'ART') or
                    starts-with($text, 'ARTICLE') or
                    starts-with($text, 'ATTACHMENT') or
                    starts-with($text, 'BOOK') or
                    starts-with($text, 'BULLETS') or
                    starts-with($text, 'BLOCKLIST') or
                    starts-with($text, 'CHAP') or
                    starts-with($text, 'CHAPTER') or
                    starts-with($text, 'CLAUSE') or
                    starts-with($text, 'CROSSHEADING') or
                    starts-with($text, 'DIVISION') or
                    starts-with($text, 'FOOTNOTE') or
                    starts-with($text, 'HEADING') or
                    starts-with($text, 'INDENT') or
                    starts-with($text, 'ITEMS') or
                    starts-with($text, 'LEVEL') or
                    starts-with($text, 'LIST') or
                    starts-with($text, 'LONGTITLE') or
                    starts-with($text, 'P{') or
                    starts-with($text, 'P.') or
                    starts-with($text, 'P ') or
                    starts-with($text, 'PARA') or
                    starts-with($text, 'PARAGRAPH') or
                    starts-with($text, 'PART') or
                    starts-with($text, 'POINT') or
                    starts-with($text, 'PROVISO') or
                    starts-with($text, 'QUOTE') or
                    starts-with($text, 'RULE') or
                    starts-with($text, 'SCHEDULE') or
                    starts-with($text, 'SEC') or
                    starts-with($text, 'SECTION') or
                    starts-with($text, 'SUBCHAP') or
                    starts-with($text, 'SUBCHAPTER') or
                    starts-with($text, 'SUBCLAUSE') or
                    starts-with($text, 'SUBDIVISION') or
                    starts-with($text, 'SUBHEADING') or
                    starts-with($text, 'SUBLIST') or
                    starts-with($text, 'SUBPARA') or
                    starts-with($text, 'SUBPARAGRAPH') or
                    starts-with($text, 'SUBPART') or
                    starts-with($text, 'SUBRULE') or
                    starts-with($text, 'SUBSEC') or
                    starts-with($text, 'SUBSECTION') or
                    starts-with($text, 'SUBTITLE') or
                    starts-with($text, 'TABLE') or
                    starts-with($text, 'TC') or
                    starts-with($text, 'TH') or
                    starts-with($text, 'TITLE') or
                    starts-with($text, 'TOME') or
                    starts-with($text, 'TR') or
                    starts-with($text, 'TRANSITIONAL')">
        <xsl:value-of select="'\'" />
      </xsl:if>
    </xsl:variable>

    <xsl:value-of select="concat($slash, $text)" />
  </xsl:template>

  <!-- adds a backslash to the start of the text param, if necessary -->
  <xsl:template name="escape">
    <xsl:param name="text"/>

    <xsl:variable name="escaped">
      <xsl:call-template name="escape-inlines">
        <xsl:with-param name="text" select="$text" />
      </xsl:call-template>
    </xsl:variable>

    <xsl:call-template name="escape-prefixes">
      <xsl:with-param name="text" select="$escaped" />
    </xsl:call-template>
  </xsl:template>

  <!-- repeats a character a certain number of times -->
  <xsl:template name="repeat">
    <xsl:param name="str" />
    <xsl:param name="count" />

    <xsl:if test="$count &gt; 0">
      <xsl:value-of select="$str" />
      <xsl:call-template name="repeat">
        <xsl:with-param name="str" select="$str" />
        <xsl:with-param name="count" select="$count - 1" />
      </xsl:call-template>
    </xsl:if>
  </xsl:template>

  <!-- indent with spaces -->
  <xsl:template name="indent">
    <xsl:param name="level" />

    <xsl:call-template name="repeat">
      <xsl:with-param name="str" select="'  '" />
      <xsl:with-param name="count" select="$level" />
    </xsl:call-template>
  </xsl:template>


  <!-- main templates -->

  <xsl:template match="html">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- bluebell-specific markers -->
  <xsl:template match="akn-block">
    <xsl:param name="indent">0</xsl:param>

    <xsl:call-template name="indent">
      <xsl:with-param name="level" select="$indent" />
    </xsl:call-template>

    <xsl:value-of select="@name" />
    <xsl:text> </xsl:text>
    <xsl:if test="@num">
      <xsl:value-of select="@num" />
    </xsl:if>
    <xsl:if test="@heading">
      <xsl:text> - </xsl:text>
      <xsl:value-of select="@heading" />
    </xsl:if>
    <xsl:if test="@subheading">
      <xsl:text>&#10;</xsl:text>
      <xsl:call-template name="indent">
        <xsl:with-param name="level" select="$indent + 1" />
      </xsl:call-template>
      <xsl:text>SUBHEADING </xsl:text>
      <xsl:value-of select="@subheading" />
    </xsl:if>
    <xsl:if test="@from">
      <xsl:text>&#10;</xsl:text>
      <xsl:call-template name="indent">
        <xsl:with-param name="level" select="$indent + 1" />
      </xsl:call-template>
      <xsl:text>FROM </xsl:text>
      <xsl:value-of select="@from" />
    </xsl:if>

    <xsl:text>&#10;&#10;</xsl:text>

    <xsl:apply-templates>
      <xsl:with-param name="indent" select="$indent + 1" />
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="akn-inline">
    <xsl:text>{{</xsl:text>
    <xsl:value-of select="@marker" />
    <xsl:apply-templates />
    <xsl:text>}}</xsl:text>
  </xsl:template>

  <!-- general html -->

  <xsl:template match="p | li">
    <xsl:param name="indent">0</xsl:param>

    <xsl:call-template name="indent">
      <xsl:with-param name="level" select="$indent" />
    </xsl:call-template>

    <xsl:apply-templates>
      <xsl:with-param name="indent" select="$indent" />
    </xsl:apply-templates>

    <!-- footnote bodies -->
    <xsl:if test=".//a[starts-with(@id, 'footnote-ref-')]">
      <xsl:text>&#10;&#10;</xsl:text>
      <xsl:apply-templates select=".//a[starts-with(@id, 'footnote-ref-')]" mode="content">
        <xsl:with-param name="indent" select="$indent" />
      </xsl:apply-templates>
    </xsl:if>

    <xsl:text>&#10;&#10;</xsl:text>
  </xsl:template>

  <!-- footnotes -->
  <!-- footnote anchors as inlines -->
  <xsl:template match="a[starts-with(@id, 'footnote-ref-')]">
    <xsl:text>{{FOOTNOTE </xsl:text>
    <xsl:value-of select=".//text()" />
    <xsl:text>}}</xsl:text>
  </xsl:template>

  <!-- footnote content -->
  <xsl:template match="a[starts-with(@id, 'footnote-ref-')]" mode="content">
    <xsl:param name="indent">0</xsl:param>

    <xsl:call-template name="indent">
      <xsl:with-param name="level" select="$indent" />
    </xsl:call-template>
    <xsl:text>FOOTNOTE </xsl:text>
    <xsl:value-of select=".//text()" />
    <xsl:text>&#10;</xsl:text>

    <!-- now find the li that contains the content for this footnote -->
    <!-- <a href="#footnote-1" id="footnote-ref-1">[1]</a> -> <li id="footnote-1"> -->
    <xsl:variable name="id" select="substring-after(@href, '#')" />
    <xsl:apply-templates select="//*[@id = $id]" mode="footnote">
      <xsl:with-param name="indent" select="$indent + 1" />
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="li[starts-with(@id, 'footnote-')]" mode="footnote">
    <xsl:param name="indent">0</xsl:param>

    <xsl:apply-templates>
      <xsl:with-param name="indent" select="$indent" />
    </xsl:apply-templates>
  </xsl:template>

  <!-- hide footnotes, they must be rendered explicitly -->
  <xsl:template match="li[starts-with(@id, 'footnote-')]" />
  <!-- don't render the arrows mammoth adds in at all -->
  <xsl:template match="a[starts-with(@href, '#footnote-ref-')]" />

  <!-- inlines -->
  <!-- ignore nested inline tags -->
  <xsl:template match="sup//sup | i//i">
    <xsl:apply-templates />
  </xsl:template>

  <xsl:template match="i">
    <xsl:text>//</xsl:text>
    <xsl:apply-templates />
    <xsl:text>//</xsl:text>
  </xsl:template>

  <xsl:template match="sup">
    <xsl:text>{{^</xsl:text>
    <xsl:apply-templates />
    <xsl:text>}}</xsl:text>
  </xsl:template>

  <!-- escape the first text nodes at the start of lines -->
  <xsl:template match="*[self::p or self::li or self::th or self::td]/text()[not(preceding-sibling::*)]">
    <xsl:call-template name="escape">
      <xsl:with-param name="text">
        <xsl:call-template name="string-ltrim">
          <xsl:with-param name="text" select="." />
        </xsl:call-template>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <!-- ...............................................................................
       Tables
       ............................................................................... -->
  <xsl:template match="table">
    <xsl:param name="indent">0</xsl:param>

    <xsl:call-template name="indent">
      <xsl:with-param name="level" select="$indent" />
    </xsl:call-template>
    <xsl:text>TABLE</xsl:text>
    <xsl:call-template name="block-attrs" />
    <xsl:text>&#10;</xsl:text>

    <xsl:apply-templates>
      <xsl:with-param name="indent" select="$indent + 1" />
    </xsl:apply-templates>
  </xsl:template>


  <xsl:template match="tr">
    <xsl:param name="indent">0</xsl:param>

    <xsl:call-template name="indent">
      <xsl:with-param name="level" select="$indent" />
    </xsl:call-template>
    <xsl:text>TR&#10;</xsl:text>

    <xsl:apply-templates>
      <xsl:with-param name="indent" select="$indent + 1" />
    </xsl:apply-templates>
  </xsl:template>


  <xsl:template match="th|td">
    <xsl:param name="indent">0</xsl:param>

    <xsl:call-template name="indent">
      <xsl:with-param name="level" select="$indent" />
    </xsl:call-template>

    <xsl:choose>
      <xsl:when test="local-name(.) = 'th'">
        <xsl:text>TH</xsl:text>
      </xsl:when>
      <xsl:when test="local-name(.) = 'td'">
        <xsl:text>TC</xsl:text>
      </xsl:when>
    </xsl:choose>

    <xsl:call-template name="block-attrs" />
    <xsl:text>&#10;</xsl:text>

    <xsl:apply-templates>
      <xsl:with-param name="indent" select="$indent + 1" />
    </xsl:apply-templates>
  </xsl:template>

  <!-- ...............................................................................
       Attribute lists at the start of marked blocks
       ............................................................................... -->

  <xsl:template name="block-attrs">
    <xsl:if test="@class">
      <xsl:text>.</xsl:text>
      <xsl:value-of select="translate(@class, ' ', '.')" />
    </xsl:if>

    <xsl:if test="@*[local-name() != 'class']">
      <xsl:text>{</xsl:text>
      <xsl:apply-templates select="@*[local-name() != 'class']" mode="generic" />
      <xsl:text>}</xsl:text>
    </xsl:if>
  </xsl:template>

  <xsl:template match="@*" mode="generic">
    <xsl:if test="position() > 1">
      <xsl:text>|</xsl:text>
    </xsl:if>
    <xsl:value-of select="local-name(.)" />
    <xsl:text> </xsl:text>
    <xsl:value-of select="." />
  </xsl:template>

  <!-- for most nodes, just dump their text content -->
  <xsl:template match="*">
    <xsl:param name="indent">0</xsl:param>
    <xsl:apply-templates>
      <xsl:with-param name="indent" select="$indent" />
    </xsl:apply-templates>
  </xsl:template>

</xsl:stylesheet>
