<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
  xmlns:a="http://www.akomantoso.org/2.0"
  exclude-result-prefixes="a">

  <xsl:output method="html" />

  <xsl:template match="a:act">
    <xsl:element name="span" namespace="">
      <xsl:attribute name="class">an-act</xsl:attribute>
      <xsl:apply-templates select="a:coverPage" />
      <xsl:apply-templates select="a:preface" />
      <xsl:apply-templates select="a:preamble" />
      <xsl:apply-templates select="a:body" />
      <xsl:apply-templates select="a:conclusions" />
    </xsl:element>
  </xsl:template>

  <!-- for parts and chapters, include an easily stylable heading -->
  <xsl:template match="a:part">
    <div class="an-part" id="{@id}">
      <h1>
        <xsl:text>Part </xsl:text>
        <xsl:value-of select="./a:num" />
        <xsl:text> - </xsl:text>
        <xsl:value-of select="./a:heading" />
      </h1>
      
      <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
    </div>
  </xsl:template>

  <xsl:template match="a:chapter">
    <div class="an-chapter" id="{@id}">
      <h1>
        <xsl:text>Chapter </xsl:text>
        <xsl:value-of select="./a:num" />
        <br/>
        <xsl:value-of select="./a:heading" />
      </h1>
      
      <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
    </div>
  </xsl:template>

  <!-- the schedules "chapter" isn't actually a chapter -->
  <xsl:template match="a:chapter[starts-with(@id, 'schedule')]">
    <div class="an-chapter" id="{@id}">
      <h1>
        <xsl:text>Schedule </xsl:text>
        <xsl:value-of select="./a:num" />
        <br/>
        <xsl:value-of select="./a:heading" />
      </h1>
      
      <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
    </div>
  </xsl:template>

  <xsl:template match="a:section">
    <div class="an-{local-name()}" id="{@id}">
      <h3>
        <xsl:value-of select="./a:num" />
        <xsl:text> </xsl:text>
        <xsl:value-of select="./a:heading" />
      </h3>
      
      <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
    </div>
  </xsl:template>
  
  <xsl:template match="a:subsection">
    <span class="an-{local-name()}" id="{@id}">
      <xsl:apply-templates select="./*[not(self::a:heading)]" />
    </span>
  </xsl:template>

  <!-- for term nodes, ensure we keep the refersTo element -->
  <xsl:template match="a:term">
    <span class="an-{local-name()}">
      <xsl:attribute name="data-refers-to">
        <xsl:value-of select="@refersTo" />
      </xsl:attribute>

      <xsl:apply-templates />
    </span>
  </xsl:template>

  <!-- for all nodes, generate a SPAN element with a class matching
       the AN name of the node and copy over the ID if it exists -->
  <xsl:template match="*">
    <span class="an-{local-name()}">
      <xsl:if test="@id">
        <xsl:attribute name="id">
          <xsl:value-of select="@id" />
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates />
    </span>
  </xsl:template>
  
  <!-- For HTML table elements, copy them over then apply normal AN
       processing to their contents -->
  <xsl:template match="a:table | a:tr | a:th | a:td">
    <xsl:element name="{local-name()}">
      <xsl:copy-of select="@*" />
      <xsl:apply-templates />
    </xsl:element>
  </xsl:template>

  <!-- special HTML elements -->
  <xsl:template match="a:a | a:abbr | a:b | a:i | a:span | a:sub | a:sup | a:u">
    <xsl:element name="{local-name()}">
      <xsl:copy-of select="@*" />
      <xsl:apply-templates />
    </xsl:element>
  </xsl:template>

</xsl:stylesheet>
