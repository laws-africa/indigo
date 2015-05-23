<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
  xmlns:a="http://www.akomantoso.org/2.0"
  exclude-result-prefixes="a">

  <xsl:output method="html" />

  <xsl:template match="a:act">
    <xsl:element name="span" namespace="">
      <xsl:attribute name="class">akn-act</xsl:attribute>
      <xsl:apply-templates select="a:coverPage" />
      <xsl:apply-templates select="a:preface" />
      <xsl:apply-templates select="a:preamble" />
      <xsl:apply-templates select="a:body" />
      <xsl:apply-templates select="a:conclusions" />
    </xsl:element>
  </xsl:template>

  <!-- for parts and chapters, include an easily stylable heading -->
  <xsl:template match="a:part">
    <div class="akn-part" id="{@id}">
      <h2>
        <xsl:text>Part </xsl:text>
        <xsl:value-of select="./a:num" />
        <xsl:text> - </xsl:text>
        <xsl:value-of select="./a:heading" />
      </h2>
      
      <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
    </div>
  </xsl:template>

  <xsl:template match="a:chapter">
    <div class="akn-chapter" id="{@id}">
      <h2>
        <xsl:text>Chapter </xsl:text>
        <xsl:value-of select="./a:num" />
        <br/>
        <xsl:value-of select="./a:heading" />
      </h2>
      
      <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
    </div>
  </xsl:template>

  <xsl:template match="a:section">
    <div class="akn-{local-name()}" id="{@id}">
      <h3>
        <xsl:value-of select="./a:num" />
        <xsl:text> </xsl:text>
        <xsl:value-of select="./a:heading" />
      </h3>
      
      <xsl:apply-templates select="./*[not(self::a:num) and not(self::a:heading)]" />
    </div>
  </xsl:template>
  
  <xsl:template match="a:subsection">
    <span class="akn-{local-name()}" id="{@id}">
      <xsl:apply-templates select="./*[not(self::a:heading)]" />
    </span>
  </xsl:template>

  <!-- for term nodes, ensure we keep the refersTo element -->
  <xsl:template match="a:term">
    <span class="akn-{local-name()}">
      <xsl:attribute name="data-refers-to">
        <xsl:value-of select="@refersTo" />
      </xsl:attribute>

      <xsl:apply-templates />
    </span>
  </xsl:template>

  <!-- components/schedules -->
  <xsl:template match="a:doc">
    <div class="akn-doc" id="{@id}">
      <xsl:if test="a:meta/a:identification/a:FRBRWork/a:FRBRalias">
        <h2>
          <xsl:value-of select="a:meta/a:identification/a:FRBRWork/a:FRBRalias/@value" />
        </h2>
      </xsl:if>

      <xsl:apply-templates select="a:coverPage" />
      <xsl:apply-templates select="a:preface" />
      <xsl:apply-templates select="a:preamble" />
      <xsl:apply-templates select="a:mainBody" />
      <xsl:apply-templates select="a:conclusions" />
    </div>
  </xsl:template>

  <!-- for all nodes, generate a SPAN element with a class matching
       the AN name of the node and copy over the ID if it exists -->
  <xsl:template match="*">
    <span class="akn-{local-name()}">
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
