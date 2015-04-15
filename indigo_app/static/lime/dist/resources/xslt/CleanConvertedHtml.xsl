<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
 <xsl:output omit-xml-declaration="yes" encoding="UTF-8"/>
 <xsl:strip-space elements="*"/>
 
 <xsl:template match="/">
  <div>
    <xsl:choose>
     <xsl:when test="//*[@id = 'main']">
      <xsl:apply-templates select="//*[@id = 'main']"/>
     </xsl:when>
     <xsl:otherwise>
      <xsl:apply-templates select="//*[name()='body']"/>
     </xsl:otherwise>
    </xsl:choose>
  </div>
 </xsl:template>
 
 <xsl:template match="*[name()='body']">
   <xsl:apply-templates />
 </xsl:template>
 
 <xsl:template match="*[@id = 'main']">
  <xsl:apply-templates />
 </xsl:template>

 <xsl:template match="*[name()='br']">
  <br/>
 </xsl:template>
 
 <xsl:template match="*[name()='p']">
  <xsl:apply-templates />
  <br/><br/>
 </xsl:template>

 <xsl:template match="*[name()='div']">
  <xsl:apply-templates />
  <br/>
 </xsl:template>
 
 <xsl:template match="*[name()='span']">
  <xsl:choose>
   <xsl:when test="contains(@class, 'footnote_reference') and not(contains(../@class, 'footnote_text'))">
    <xsl:element name="{name()}">
      <xsl:attribute name="class">
          <xsl:value-of select="'noteRefNumber'"/>
      </xsl:attribute>
      <xsl:apply-templates />
    </xsl:element>
   </xsl:when>
   <xsl:otherwise>
      <xsl:apply-templates />
   </xsl:otherwise>
  </xsl:choose>
 </xsl:template>

 <xsl:template match="*[name()='ol']">
  <xsl:element name="{name()}">
     <xsl:attribute name="class">
      <xsl:value-of select="'toMark'"/>
     </xsl:attribute>
    <xsl:apply-templates />
   </xsl:element>
 </xsl:template>

 <xsl:template priority="1" match="*[name()='h1' or name()='h2' or name()='h3' or name()='h4' or name()='h5' or name()='h6']">
  <xsl:apply-templates />
 </xsl:template>

 <xsl:template priority="1" match="*[(name()='a' or name()='span' or name()='p') and ./*[name()='table']]">
  <div>
    <xsl:apply-templates select="./*[name()='table']/preceding-sibling::node()"/>
  </div>
  <xsl:apply-templates select="./*[name()='table']"/>
  <div>
    <xsl:apply-templates select="./*[name()='table']/following-sibling::node()"/>
  </div>
 </xsl:template>
 
 <xsl:template match="*[not(name()='a') and not(name()='body') and not(name()='br') and not(name()='p') and not(name()='span') and not(name()='div') and not(name()='ol')]">
  <xsl:if test="not(.='')">
   <xsl:element name="{name()}">
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