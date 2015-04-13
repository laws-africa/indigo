<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
 <xsl:output omit-xml-declaration="yes"
  doctype-public="-//ABISOURCE//DTD XHTML plus AWML 2.2//EN"
  doctype-system="http://www.abisource.com/2004/xhtml-awml/xhtml-awml.mod" encoding="UTF-8"/>
 <xsl:strip-space elements="*"/>
 
 <xsl:template match="/">
  <xsl:apply-templates select="//*[name()='body']"/> 
 </xsl:template>
 
 <xsl:template match="*[name()='body']">
  <xsl:apply-templates />
 </xsl:template>
 
 <xsl:template match="*[name()='br']">
  <br/>
 </xsl:template>
 
 <xsl:template match="*[@id = 'header']">
 </xsl:template>
 
 <xsl:template match="*[@id = 'footer']">
 </xsl:template>
 
 <xsl:template match="*[@class = 'zyan-feld']">
 </xsl:template>
 
 <xsl:template match="*[@class = 'footnote_text']">
 </xsl:template>
 
 <xsl:template match="*[@class = 'footnote_text']" mode="replaceNote">
  <xsl:apply-templates  select="./*[position()=last()]"/>
 </xsl:template>
 
 <xsl:template match="*[@class = 'footnote_reference']">
  <xsl:if test="not(.='')">
   <xsl:element name="{name()}">
    <xsl:variable name="baseClass" select="'toMark'" />
    <xsl:variable name="noteId" select="@id" />
    <xsl:attribute name="class">
     <xsl:value-of select="concat($baseClass, ' authorialNote')"/>
    </xsl:attribute>
    <xsl:for-each select="@*[not(name() = 'class') and
     not(name() = 'style') and 
     not(name() = 'lang') and
     not(name() = 'xml:lang') and 
     not(name() = 'dir') and 
     not(contains(name(), 'awml'))]">
     <xsl:attribute name="{name()}">
      <xsl:value-of select="."/>
     </xsl:attribute>
    </xsl:for-each>
    <xsl:apply-templates  mode="replaceNote" select="//*[@class = 'footnote_text'][.//*[@href=concat('#', $noteId)]]"/>
    <!-- <xsl:apply-templates /> -->
   </xsl:element>
  </xsl:if>
 </xsl:template>
 
 
 <xsl:template match="*[not(name()='a') and 
                        not(name()='body') and
                        not(name()='br') and
                        not(@id = 'header') and
                        not(@id = 'footer') and
                        not(@class = 'zyan-feld')and
                        not(@class = 'footnote_text') and
                        not(@class = 'footnote_reference')]">
  <xsl:if test="not(.='')">
   <xsl:element name="{name()}">
    <xsl:variable name="baseClass" select="'toMark'" />
    <xsl:choose>
     <xsl:when test="@class = 'berschrift_9'">
      <xsl:attribute name="class">
       <xsl:value-of select="concat($baseClass, ' partitionHeader')"/>
      </xsl:attribute>
     </xsl:when>
     <xsl:when test="@class = 'erlass_titel'">
      <xsl:attribute name="class">
       <xsl:value-of select="concat($baseClass, ' docTitle')"/>
      </xsl:attribute>
     </xsl:when>
     <xsl:when test="@class = 'erlass_datum'">
      <xsl:attribute name="class">
       <xsl:value-of select="concat($baseClass, ' docDate')"/>
      </xsl:attribute>
     </xsl:when>
     <xsl:when test="@class = 'erlass_datum'">
      <xsl:attribute name="class">
       <xsl:value-of select="concat($baseClass, ' docDate')"/>
      </xsl:attribute>
     </xsl:when>
     <xsl:when test="@class = 'autor'">
      <xsl:attribute name="class">
       <xsl:value-of select="concat($baseClass, ' docIntroducer')"/>
      </xsl:attribute>
     </xsl:when>
     <xsl:when test="@class = 'ingress'">
      <xsl:attribute name="class">
       <xsl:value-of select="concat($baseClass, ' preamble')"/>
      </xsl:attribute>
     </xsl:when>
     <xsl:when test="@class = 'absatz'">
      <xsl:attribute name="class">
       <xsl:value-of select="concat($baseClass, ' paragraph')"/>
      </xsl:attribute>
     </xsl:when>
     <xsl:when test="@class = 'verb'">
      <xsl:attribute name="class">
       <xsl:value-of select="concat($baseClass, ' formula')"/>
      </xsl:attribute>
     </xsl:when>
     <xsl:otherwise>
     </xsl:otherwise>
    </xsl:choose>
    <xsl:for-each select="@*[not(name() = 'class') and
     not(name() = 'style') and 
     not(name() = 'lang') and
     not(name() = 'xml:lang') and 
     not(name() = 'dir') and 
     not(contains(name(), 'awml'))]">
     <xsl:attribute name="{name()}">
      <xsl:value-of select="."/>
     </xsl:attribute>
    </xsl:for-each>
    <xsl:apply-templates />
   </xsl:element>
  </xsl:if>
 </xsl:template>
</xsl:stylesheet>