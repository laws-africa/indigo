<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:a="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                exclude-result-prefixes="a">

  <xsl:output method="xml" encoding="utf8" />

  <!-- in num nuke term, or any other intervening tag, but keep their text as a direct child -->
  <xsl:template match="a:num[a:*]">
    <num>
      <xsl:apply-templates select=".//text()" />
    </num>
  </xsl:template>

  <!-- unwrap hcontainers -->
  <xsl:template match="a:*[self::a:part or self::a:section or self::a:article or self::a:chapter or self::a:subsection
                           or self::a:subpart or self::a:division or self::a:paragraph or self::a:subparagraph]/a:hcontainer[@name='hcontainer']">
    <xsl:choose>
      <!-- strip hcontainer completely when it's the only content element in a hier element -->
      <xsl:when test="preceding-sibling::a:*[1][self::a:num or self::a:heading or self::a:subheading] and not(following-sibling::a:*)">
        <xsl:apply-templates select="a:content" />
      </xsl:when>

      <!-- change hcontainer into intro when it's the first content element in a hier element -->
      <xsl:when test="preceding-sibling::a:*[1][self::a:num or self::a:heading or self::a:subheading] and following-sibling::a:*">
        <intro>
          <xsl:apply-templates select="a:content/*" />
        </intro>
      </xsl:when>

      <!-- change hcontainer into wrapUp when it's the last content element in a hier element -->
      <xsl:when test="not(preceding-sibling::a:*[1][self::a:num or self::a:heading or self::a:subheading]) and not(following-sibling::a:*)">
        <wrapUp>
          <xsl:apply-templates select="a:content/*" />
        </wrapUp>
      </xsl:when>

      <!-- keep it -->
      <xsl:otherwise>
        <xsl:copy>
          <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- strip hcontainer completely when it's the in the mainBody element -->
  <xsl:template match="a:mainBody/a:hcontainer[@name='hcontainer']">
    <xsl:apply-templates select="a:content/a:*" />
  </xsl:template>

  <!-- legacy bluebell had hcontainer without content :( -->
  <xsl:template match="a:hcontainer[@name='hcontainer' and a:p]">
    <hcontainer name="hcontainer">
      <content>
        <xsl:apply-templates />
      </content>
    </hcontainer>
  </xsl:template>

  <!-- remove unnecessary placeholder p's in hierarchical elements -->
  <xsl:template match="a:*[self::a:subsection or self::a:section or self::a:paragraph or self::a:article]/a:content[
                         a:p[not(node()) and not(preceding-sibling::*) and not(following-sibling::*)]]" />

  <!-- crossHeadings at the top level must be wrapped in hcontainer -->
  <xsl:template match="a:body/a:crossHeading | a:mainBody/a:crossHeading">
    <hcontainer name="hcontainer">
      <crossHeading>
        <xsl:apply-templates />
      </crossHeading>
    </hcontainer>
  </xsl:template>

  <!-- attachments can't have empty bodies -->
  <xsl:template match="a:attachment/a:doc/a:mainBody[not(node())]">
    <mainBody>
      <p/>
    </mainBody>
  </xsl:template>

  <!-- ignore some empty elements -->
  <xsl:template match="a:*[self::a:preface or self::a:preamble or self::a:conclusions or self::a:i or self::a:b
                           or self::a:listIntroduction or self::a:attachments][not(node())]" />

  <!-- hcontainers with empty content need a p -->
  <xsl:template match="a:hcontainer/a:content[not(node())]">
    <content>
      <p eId="hcontainer_1__p_1"/>
    </content>
  </xsl:template>

  <!-- remove empty p tags at the start and end of table cells -->
  <xsl:template match="a:*[self::a:th or self::a:td]/a:p[not(node()) and not(preceding-sibling::a:*) and following-sibling::a:*]" />
  <xsl:template match="a:*[self::a:th or self::a:td]/a:p[not(node()) and preceding-sibling::a:* and not(following-sibling::a:*)]" />

  <!-- ensure FRBRalias has name="title" -->
  <xsl:template match="a:FRBRalias[not(@name)]">
    <xsl:copy>
      <xsl:attribute name="name">title</xsl:attribute>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

  <!-- remove slaw and council entries -->
  <xsl:template match="a:TLCOrganization[@eId='slaw']" />
  <xsl:template match="a:TLCOrganization[@eId='council']" />
  <xsl:template match="a:TLCRole[@eId='author']" />

  <!-- provide a value for empty publication dates -->
  <xsl:template match="a:publication/@date[. = '']">
    <xsl:attribute name="date">0001-01-01</xsl:attribute>
  </xsl:template>

  <!-- clear out FRBRAuthor -->
  <xsl:template match="a:FRBRauthor/@href[. != '']">
    <xsl:attribute name="href" />
  </xsl:template>
  <xsl:template match="a:FRBRauthor/@as[. = '#author']" />

  <!-- remove empty p tags that are not alone in items -->
  <xsl:template match="a:item/a:p[not(node()) and preceding-sibling::a:*[1][self::a:num or self::a:heading or self::a:subheading]
                       and following-sibling::a:*]" />

  <!-- replace empty bodies -->
  <xsl:template match="a:body[not(a:*)]">
    <body>
      <hcontainer eId="hcontainer_1" name="hcontainer">
        <content>
          <p eId="hcontainer_1__p_1"/>
	      </content>
	    </hcontainer>
	  </body>
  </xsl:template>

  <!-- ensure act[@contains="singleVersion"] -->
  <xsl:template match="a:*[self::a:act or self::a:doc][not(@contains)]">
    <xsl:copy>
      <xsl:choose>
        <xsl:when test="a:meta/a:lifecycle/a:eventRef[@name='amendment']">
          <xsl:attribute name="contains">singleVersion</xsl:attribute>
        </xsl:when>
      </xsl:choose>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="a:*[self::a:act or self::a:doc]/@contains[. = 'originalVersion']" />

  <!-- statements must have a name -->
  <xsl:template match="a:statement[not(@name)]">
    <xsl:copy>
      <xsl:attribute name="name">statement</xsl:attribute>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

  <!-- remove empty rowSpan and colSpan -->
  <xsl:template match="a:*[self::a:th or self::a:td]/@rowspan[. = '']" />
  <xsl:template match="a:*[self::a:th or self::a:td]/@colspan[. = '']" />

  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
