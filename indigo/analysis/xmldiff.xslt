<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:diff="http://namespaces.shoobx.com/diff"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- These attributes indicate a whole element was inserted or deleted.
       Xmldiff sometimes includes further inserts and deletes inside them,
       when it copies and then modifies an element into a new position. -->

  <!-- An additional insert inside an existing insert can be ignored (attribute is removed) -->
  <xsl:template match="*[@diff:insert]//*/@diff:insert" />
  <!-- A deletion inside an insert must be removed completely -->
  <xsl:template match="*[@diff:insert]//*[@diff:delete]" />
  <!-- An insert inside a delete doesn't make sense and can be removed completely -->
  <xsl:template match="*[@diff:delete]//*[@diff:insert]" />
  <!-- An additional delete inside an existing delete can be ignored (attribute is removed) -->
  <xsl:template match="*[@diff:delete]//*/@diff:delete" />

  <!-- Inline text inserted inside an insert must be retained -->
  <xsl:template match="*[@diff:insert]//diff:insert">
    <xsl:apply-templates/>
  </xsl:template>
  <!-- Inline text deleted inside an insert must be removed -->
  <xsl:template match="*[@diff:insert]//diff:delete"/>
  <!-- Inline text inserted inside a delete doesn't make sense and can be ignored -->
  <xsl:template match="*[@diff:delete]//diff:insert"/>
  <!-- Inline text deleted inside a delete must be retained -->
  <xsl:template match="*[@diff:delete]//diff:delete">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- we don't care about attribute changes -->
  <xsl:template match="@diff:add-attr | @diff:remove-attr | @diff:update-attr" />

  <xsl:template match="@diff:insert-formatting">
    <xsl:attribute name="class">
      <xsl:value-of select="'ins'"/>
    </xsl:attribute>
  </xsl:template>

  <!-- we can't change an existing class attribute, so copy it to classx and then python will move classx to class -->
  <xsl:template match="@diff:insert">
    <xsl:attribute name="classx">
      <xsl:value-of select="'ins '"/>
      <xsl:value-of select="../@class"/>
    </xsl:attribute>
  </xsl:template>

  <!-- we can't change an existing class attribute, so copy it to classx and then python will move classx to class -->
  <xsl:template match="@diff:delete">
    <xsl:attribute name="classx">
      <xsl:value-of select="'del '"/>
      <xsl:value-of select="../@class"/>
    </xsl:attribute>
  </xsl:template>

  <!-- inline text was deleted -->
  <xsl:template match="diff:delete">
    <del><xsl:apply-templates /></del>
  </xsl:template>

  <!-- inline text was inserted -->
  <xsl:template match="diff:insert">
    <ins><xsl:apply-templates /></ins>
  </xsl:template>

  <xsl:template match="@* | node()">
    <xsl:copy>
      <xsl:apply-templates select="@* | node()"/>
    </xsl:copy>
  </xsl:template>
</xsl:stylesheet>
