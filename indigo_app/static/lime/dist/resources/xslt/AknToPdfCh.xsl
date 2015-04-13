<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" 
    xmlns:fo="http://www.w3.org/1999/XSL/Format"
    xmlns:id="http://www.cs.unibo.it/~fabio/iml/id"
    xmlns:ch="http://www.admin.ch/ns/akn20">
    
    
    <!-- TODO: uniform px/pt xmlns:akn="http://www.akomantoso.org/2.0" -->
    <xsl:param name="startPageNumber">1</xsl:param>
    
    <xsl:template match="/">
        <fo:root xmlns:fo="http://www.w3.org/1999/XSL/Format"
            xmlns:id="http://www.cs.unibo.it/~fabio/iml/id">
            <fo:layout-master-set>
                <fo:simple-page-master page-width="595.28pt" page-height="841.89pt" master-name="first-page">
                    <fo:region-body region-name="xsl-region-body" margin-top="56.913pt"
                        margin-right="46.20pt" margin-left="112.205pt"
                        margin-bottom="66.67pt" 
                    />
                    <fo:region-before region-name="first-page-xsl-region-before" extent="73.713pt"
                        display-align="after"/>
                    <fo:region-after region-name="first-page-xsl-region-after" extent="55.49pt"
                        display-align="before"/>
                </fo:simple-page-master>
                <fo:simple-page-master page-width="595.28pt" page-height="841.89pt" master-name="odd-pages">
                    <fo:region-body region-name="xsl-region-body" margin-top="99.213pt"
                        margin-right="46.20pt" margin-left="112.205pt"
                        margin-bottom="66.67pt" 
                    />
                    <fo:region-before region-name="odd-xsl-region-before" extent="73.713pt"
                        display-align="after"/>
                    <fo:region-after region-name="odd-xsl-region-after" extent="55.49pt"
                        display-align="before"/>
                </fo:simple-page-master>
                <fo:simple-page-master page-width="595.28pt" page-height="841.89pt" master-name="even-pages">
                    <fo:region-body region-name="xsl-region-body" margin-top="99.213pt"
                        margin-right="46.205pt" margin-left="50.20pt"
                        margin-bottom="66.67pt" 
                    />
                    <fo:region-before region-name="even-xsl-region-before" extent="73.713pt"
                        display-align="after"/>
                    <fo:region-after region-name="even-xsl-region-after" extent="55.49pt"
                        display-align="before"/>
                </fo:simple-page-master>
                <fo:simple-page-master page-width="595.28pt" page-height="841.89pt" master-name="empty-page">
                    <fo:region-body region-name="xsl-region-body" margin-top="99.213pt"
                        margin-right="46.205pt" margin-left="82.20pt"
                        margin-bottom="66.67pt" 
                    />
                </fo:simple-page-master>
                
                <fo:simple-page-master page-height="595.28pt" page-width="841.89pt" master-name="landscape">
                    <fo:region-body region-name="xsl-region-body" margin-right="50pt"
                        margin-top="90pt" margin-bottom="6.205pt" margin-left="36pt"/>
                    <fo:region-before region-name="landscape-xsl-region-before" extent="75.49pt"
                        display-align="after"/>
                    <fo:region-after region-name="landscape-xsl-region-after" extent="55pt"
                        display-align="before"/>
                </fo:simple-page-master>
                
                <fo:simple-page-master page-width="595.28pt" page-height="841.89pt" master-name="compendio-page">
                    <fo:region-body region-name="xsl-region-body" margin-top="99.213pt"
                        margin-right="112.205pt" margin-left="50.20pt" margin-bottom="66.67pt"/>
                    <fo:region-before region-name="compendio-xsl-region-before" extent="73.713pt"
                        display-align="after"/>
                    <fo:region-after region-name="compendio-xsl-region-after" extent="55.49pt"
                        display-align="before"/>
                </fo:simple-page-master>
                
                <fo:page-sequence-master master-name="all-pages">
                    <fo:repeatable-page-master-alternatives>
                        <fo:conditional-page-master-reference page-position="first" odd-or-even="any"
                            master-reference="first-page"/>
                        <fo:conditional-page-master-reference odd-or-even="even"
                            master-reference="even-pages" blank-or-not-blank="any"/>
                        <fo:conditional-page-master-reference odd-or-even="odd" master-reference="odd-pages"
                            blank-or-not-blank="any"/>
                    </fo:repeatable-page-master-alternatives>
                </fo:page-sequence-master>
                
                <fo:page-sequence-master master-name="landscape-pages">
                    <fo:single-page-master-reference master-reference="landscape"/>
                </fo:page-sequence-master>
                
                <fo:page-sequence-master master-name="compendio-pages">
                    <fo:single-page-master-reference master-reference="compendio-page"/>
                </fo:page-sequence-master>
            </fo:layout-master-set>
            
            
           <xsl:apply-templates/>
            
            
        </fo:root>
    </xsl:template>
    
    
    <xsl:template match="akn:doc[@name='allegato']">
        <fo:page-sequence format="1" master-reference="landscape-pages" force-page-count="no-force"
            initial-page-number="{$startPageNumber}" language="en">
            <fo:static-content flow-name="landscape-xsl-region-after">
                <fo:block margin-right="46.20pt" margin-left="36pt" text-align-last="justify"
                    text-align="justify" font-style="normal" font-size="12pt" font-family="LucidaSans"
                    ><fo:page-number/><fo:leader
                        leader-pattern="space"/><fo:inline font-family="LucidaSans" font-size="9pt"/></fo:block>
            </fo:static-content>
            <fo:static-content flow-name="landscape-xsl-region-before" margin-right="46.20pt"
                margin-left="36pt">
                <fo:table border-bottom-width="1px" border-bottom-color="black"
                    border-bottom-style="solid" padding-bottom="4px" width="750pt">
                    <fo:table-column column-width="300pt"/>
                    <fo:table-column column-width="136pt"/>
                    <fo:table-body>
                        <fo:table-row padding="0px">
                            <fo:table-cell text-align="left" padding="0px" margin="0px">
                                <fo:block font-style="normal" margin="0px" font-family="TimesNewRoman"
                                    padding="0px" padding-bottom="4px" font-size="11pt">
                                    
                                    <xsl:value-of select=".//ch:oddPageHeading/ch:left"/>
                                    
                                </fo:block>
                            </fo:table-cell>
                            <fo:table-cell text-align="right" padding="0pt" margin="0pt">
                                <fo:block margin="0pt" padding="0pt" font-family="TimesNewRoman"
                                    font-size="13pt" font-weight="bold"> </fo:block>
                            </fo:table-cell>
                        </fo:table-row>
                    </fo:table-body>
                </fo:table>
            </fo:static-content>
            <fo:flow widows="2" text-align="justify" orphans="2" font-family="TimesNewRoman"
                flow-name="xsl-region-body" word-spacing.minimum="-1pt" word-spacing.optimum="0pt"
                word-spacing.maximum="2pt">
                <xsl:apply-templates select="akn:*"/>
            </fo:flow>
        </fo:page-sequence>
        
     
    </xsl:template>
    
    
    <xsl:template match="akn:doc[@name='compendium']">
        <fo:page-sequence format="1" master-reference="compendio-pages" force-page-count="no-force"
            initial-page-number="1">
            <fo:static-content flow-name="compendio-xsl-region-before" margin-left="46.20pt"
                margin-right="112.205pt">
                <fo:block border-bottom="1px solid black"/>	
            </fo:static-content>
            <fo:static-content flow-name="compendio-xsl-region-after">
                <fo:block margin-left="46.20pt" margin-right="112.205pt" text-align="left"
                    font-style="normal" font-size="11pt" font-family="LucidaSans" border-top="1px solid black" padding-top="9px"
                    ><fo:page-number/></fo:block>
            </fo:static-content>
            <fo:static-content flow-name="xsl-footnote-separator">
                <fo:block line-height="23.6pt" font-size="21.6pt" font-family="TimesNewRoman"
                    color="white">x</fo:block>
            </fo:static-content>
            <fo:flow widows="2" text-align="justify" orphans="2" font-family="TimesNewRoman"
                flow-name="xsl-region-body" word-spacing.minimum="-1pt" word-spacing.optimum="0pt"
                word-spacing.maximum="2pt">
                <xsl:apply-templates/>
            </fo:flow>
        </fo:page-sequence>
    </xsl:template>
    
    <xsl:template match="akn:doc | akn:bill | akn:act">
        <fo:page-sequence format="1" master-reference="all-pages" force-page-count="even"
            initial-page-number="{$startPageNumber}" language="en" country="GB">
            <!-- TODO: use fo:block-container (absolute position) instead of tables?does FOP support it? -->
            <!-- TODO: add support for ch:firstPageHeading -->
            <fo:static-content flow-name="first-page-xsl-region-before">
                <fo:block margin-right="46.20pt" margin-left="112.205pt"
                    text-align-last="justify" text-align="justify" font-style="normal" font-size="11pt"
                    font-family="LucidaSans"></fo:block>
            </fo:static-content>
            <fo:static-content flow-name="first-page-xsl-region-after">
                <fo:block margin-right="46.20pt" margin-left="112.205pt"
                    text-align-last="justify" text-align="justify" font-style="normal" font-size="11pt"
                    font-family="LucidaSans">
                    <fo:inline font-family="LucidaSans" font-size="9pt"><xsl:apply-templates select="//akn:docketNumber"/></fo:inline>
                    <fo:leader leader-pattern="space"/>
                    <fo:page-number/>
                </fo:block>
            </fo:static-content>
            <fo:static-content flow-name="odd-xsl-region-before" margin-right="46.20pt"
                margin-left="112.205pt">
                <fo:table border-bottom-width="1px" border-bottom-color="black"
                    border-bottom-style="solid" padding-bottom="4px" width="436pt">
                    <xsl:choose>
                        <xsl:when test=".//ch:oddPageHeading/ch:left[contains(@class,'one-third')]">
                            <fo:table-column column-width="136pt"/>
                            <fo:table-column column-width="300pt"/>
                        </xsl:when>
                        <xsl:when test=".//ch:oddPageHeading/ch:left[contains(@class,'two-third')]">
                            <fo:table-column column-width="300pt"/>
                            <fo:table-column column-width="136pt"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <fo:table-column column-width="168pt"/>
                            <fo:table-column column-width="168pt"/>
                        </xsl:otherwise>
                    </xsl:choose>
                    
                    <fo:table-body>
                        <fo:table-row padding="0px">
                            <fo:table-cell   text-align="left" padding="0px" margin="0px">
                                <fo:block font-style="normal" margin="0px"
                                    font-family="TimesNewRoman" padding="0px"
                                    padding-bottom="4px">
                                    <xsl:attribute name="font-size">
                                        <xsl:choose>
                                            <xsl:when test=".//ch:oddPageHeading/ch:left[contains(@class,'bigger')]">13pt</xsl:when>
                                            <xsl:otherwise>11pt</xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:attribute>
                                    
                                    <xsl:if test=".//ch:oddPageHeading/ch:left[contains(@class,'bold')]">
                                        <xsl:attribute name="font-weight">bold</xsl:attribute>
                                    </xsl:if>
                                    <xsl:value-of select=".//ch:oddPageHeading/ch:left"/>
                                </fo:block>
                            </fo:table-cell>
                            <fo:table-cell text-align="right" padding="0pt" margin="0pt">
                                <fo:block margin="0pt" padding="0pt" font-family="TimesNewRoman">
                                    <xsl:attribute name="font-size">
                                        <xsl:choose>
                                            <xsl:when test=".//ch:oddPageHeading/ch:right[contains(@class,'bigger')]">13pt</xsl:when>
                                            <xsl:otherwise>11pt</xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:attribute>
                                    <xsl:if test=".//ch:oddPageHeading/ch:right[contains(@class,'bold')]">
                                        <xsl:attribute name="font-weight">bold</xsl:attribute>
                                    </xsl:if>
                                    <xsl:value-of select=".//ch:oddPageHeading/ch:right"/>
                                </fo:block>
                            </fo:table-cell>
                        </fo:table-row>
                    </fo:table-body>
                </fo:table>
            </fo:static-content>
            <fo:static-content flow-name="odd-xsl-region-after">
                <fo:block  margin-right="46.20pt" margin-left="112.205pt" text-align="right"
                    font-style="normal" font-size="11pt" font-family="LucidaSans">
                    <fo:page-number/>
                </fo:block>
            </fo:static-content>
            <fo:static-content flow-name="even-xsl-region-before" margin-left="46.20pt"
                margin-right="112.205pt">
                <fo:table border-bottom-width="1px" border-bottom-color="black"
                    border-bottom-style="solid" padding-bottom="4px" width="436pt">
                    <xsl:choose>
                        <xsl:when test=".//ch:evenPageHeading/ch:left[contains(@class,'one-third')]">
                            <fo:table-column column-width="136pt"/>
                            <fo:table-column column-width="300pt"/>
                        </xsl:when>
                        <xsl:when test=".//ch:evenPageHeading/ch:left[contains(@class,'two-third')]">
                            <fo:table-column column-width="300pt"/>
                            <fo:table-column column-width="136pt"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <fo:table-column column-width="168pt"/>
                            <fo:table-column column-width="168pt"/>
                        </xsl:otherwise>
                    </xsl:choose>
                    <fo:table-body>
                        <fo:table-row padding="0px">
                            <fo:table-cell text-align="left" padding="0px" margin="0px">
                                <fo:block font-style="normal" margin="0px" 
                                    font-family="TimesNewRoman" padding="0px">
                                    <xsl:attribute name="font-size">
                                        <xsl:choose>
                                            <xsl:when test=".//ch:evenPageHeading/ch:left[contains(@class,'bigger')]">13pt</xsl:when>
                                            <xsl:otherwise>11pt</xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:attribute>
                                    <xsl:if test=".//ch:evenPageHeading/ch:left[contains(@class,'bold')]">
                                        <xsl:attribute name="font-weight">bold</xsl:attribute>
                                    </xsl:if>
                                    <xsl:value-of select=".//ch:evenPageHeading/ch:left"/>
                                </fo:block>
                            </fo:table-cell>
                            <fo:table-cell text-align="right" padding="0pt" margin="0pt">
                                <fo:block margin="0pt" padding="0pt" font-family="TimesNewRoman" padding-bottom="4px"
                                    >
                                    <xsl:attribute name="font-size">
                                        <xsl:choose>
                                            <xsl:when test=".//ch:evenPageHeading/ch:right[contains(@class,'bigger')]">13pt</xsl:when>
                                            <xsl:otherwise>11pt</xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:attribute>
                                    <xsl:if test=".//ch:evenPageHeading/ch:right[contains(@class,'bold')]">
                                        <xsl:attribute name="font-weight">bold</xsl:attribute>
                                    </xsl:if>
                                    <xsl:value-of select=".//ch:evenPageHeading/ch:right"/>
                                </fo:block>
                            </fo:table-cell>
                        </fo:table-row>
                    </fo:table-body>
                </fo:table>
            </fo:static-content>
            <fo:static-content flow-name="even-xsl-region-after">
                <fo:block  margin-left="46.20pt" margin-right="112.205pt" text-align="left"
                    font-style="normal" font-size="11pt" font-family="LucidaSans">
                    <fo:page-number/>
                </fo:block>
            </fo:static-content>
            <fo:static-content flow-name="xsl-footnote-separator">
                <fo:block line-height="23.6pt" font-size="21.6pt" font-family="TimesNewRoman"
                    color="white">x</fo:block>
            </fo:static-content>
            <fo:flow widows="2" text-align="justify" orphans="2" font-family="TimesNewRoman"
                flow-name="xsl-region-body" word-spacing.minimum="-1pt" word-spacing.optimum="0pt"
                word-spacing.maximum="2pt">
                <xsl:choose>
                    <xsl:when test=".//akn:p"><xsl:apply-templates select="akn:*"/></xsl:when>
                    <xsl:otherwise>
                        <fo:block start-indent="0pt" space-after="6pt"  line-stacking-strategy="font-height"
                            line-height="17pt" hyphenate="false" font-size="12.5pt" 
                            language="en" country="US" text-align="justify">
                            EMPTY DOCUMENT.
                        </fo:block> 
                    </xsl:otherwise>
                </xsl:choose>
                
                
                
            </fo:flow>
        </fo:page-sequence>     
        
        
    </xsl:template>
    
    
    <xsl:template match="akn:documentCollection">
        <fo:page-sequence format="1" master-reference="all-pages" force-page-count="no-force"
            initial-page-number="{$startPageNumber}" language="en" country="GB">
            <fo:static-content flow-name="first-page-xsl-region-before">
                <fo:block margin-right="46.20pt" margin-left="112.205pt"
                    text-align-last="justify" text-align="justify" font-style="normal" font-size="11pt"
                    font-family="LucidaSans"></fo:block>
            </fo:static-content>
            <fo:static-content flow-name="first-page-xsl-region-after">
                <fo:block margin-right="46.20pt" margin-left="112.205pt"
                    text-align-last="justify" text-align="justify" font-style="normal" font-size="11pt"
                    font-family="LucidaSans">
                    <fo:inline font-family="LucidaSans" font-size="9pt"><xsl:apply-templates select="//akn:docketNumber"/></fo:inline>
                    <fo:leader leader-pattern="space"/>
                    <fo:page-number/>
                </fo:block>
            </fo:static-content>
            <fo:static-content flow-name="xsl-footnote-separator">
                <fo:block line-height="23.6pt" font-size="21.6pt" font-family="TimesNewRoman"
                    color="white">x</fo:block>
            </fo:static-content>
            <fo:flow widows="2" text-align="justify" orphans="2" font-family="TimesNewRoman"
                flow-name="xsl-region-body" word-spacing.minimum="-1pt" word-spacing.optimum="0pt"
                word-spacing.maximum="2pt">                
                <xsl:apply-templates select="akn:*[not(name() = 'collectionBody')]"/>
                
                <!-- Issue: preface per l'intera documentCollection ma la prima component va nella stessa pagina -->
                <xsl:variable name="idRef" select="substring-after(akn:collectionBody/akn:componentRef[1]/@src,'#')"/>
                <xsl:apply-templates select="//akn:component[@id = $idRef]/akn:doc/akn:*"/>
            </fo:flow>
        </fo:page-sequence>     
        
        <xsl:for-each select="akn:collectionBody/akn:componentRef[position() &gt; 1]">
            <xsl:variable name="idRef" select="substring-after(@src,'#')"/>
            <xsl:apply-templates select="//akn:component[@id = $idRef]"/>
        </xsl:for-each>
        
    </xsl:template>
    
    
    <!-- ============================================== -->
    <!--                    Collection                  -->
    <!-- ============================================== -->
    <xsl:template match="akn:components"/>
    
    
    <!-- ============================================== -->
    <!--              meta: not displayed               -->
    <!-- ============================================== -->
    <xsl:template match="akn:meta"/>
    
    
    
    <!-- ============================================== -->
    <!--                  Preface                       -->
    <!-- ============================================== -->    
    <xsl:template match="akn:preface">
        <xsl:choose>
            <xsl:when test="ancestor::akn:doc[@name='allegato']"></xsl:when>
            <xsl:when test="ancestor::akn:doc[@name='compendium'] or ancestor::akn:doc[@name='message']"><xsl:apply-templates/></xsl:when>
            <xsl:otherwise>
                <fo:block-container space-after.precedence="force" space-after="20pt"
                    border-bottom-style="solid" border-bottom-width="1px" border-bottom-color="black">
                    <xsl:if test="count(akn:p) &lt; 2 and not(contains(@class,'horizontal'))">
                        <xsl:attribute name="height">100pt</xsl:attribute>
                    </xsl:if>
                    <xsl:apply-templates/>
                </fo:block-container>
            </xsl:otherwise>
        </xsl:choose>
       
    </xsl:template>
    
    <!-- docTitle (in paragraph) -->
    <xsl:template match="akn:p[akn:docTitle]">
        <fo:block text-transform="none" text-align="left"  line-height="14pt" hyphenate="false" font-weight="bold" font-style="normal"
            space-after="22pt" margin-right="30pt">
            
            <xsl:choose>
                <xsl:when test=".//akn:*[@class='bigger'] or ancestor::akn:doc[@name='compendium']">
                    <xsl:attribute name="font-size">14pt</xsl:attribute>
                    <xsl:attribute name="line-height">14pt</xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:attribute name="font-size">17pt</xsl:attribute>
                    <xsl:attribute name="line-height">17pt</xsl:attribute>
                </xsl:otherwise>
            </xsl:choose>
            
            
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>
    
    <!-- docNumber (in paragraph) -->
    <xsl:template match="akn:p[akn:docNumber]">
        <fo:block text-transform="none" text-align="right"  line-height="14pt" hyphenate="false" font-weight="bold" font-style="normal"
            font-size="17pt" space-after="0pt" margin-top="0pt" space-before="0pt">
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>

    <!-- ============================================== -->
    <!--                    Chapter                     -->
    <!-- ============================================== -->
    <!-- TODO: use this approach also for article/point and al other hcontainer(s) -->
    <xsl:template match="akn:chapter | akn:subchapter">
        <fo:block start-indent="0pt" space-after="8pt"
            line-height="14pt" hyphenate="false" font-size="14pt" 
            keep-with-next="always"
            font-weight="bold"
            font-style="normal" keep-with-next.within-page="always">
            <fo:inline>
                <xsl:attribute name="padding-right">
                <xsl:choose>
                    <xsl:when test="name()='chapter'">100px</xsl:when>
                    <xsl:otherwise>85px</xsl:otherwise>
                </xsl:choose>
                </xsl:attribute>
                
                <xsl:apply-templates select="akn:num/* | akn:num/text()"/></fo:inline>
            <fo:inline><xsl:apply-templates select="akn:heading/* | akn:heading/text()"/></fo:inline>
        </fo:block>
        <xsl:apply-templates select="akn:*[not(name()='num' or name()='heading')]"/>
    </xsl:template>
    
    
    
    
    <!-- ============================================== -->
    <!--                    Articles                    -->
    <!-- ============================================== -->
    <xsl:template match="akn:article">
        <xsl:apply-templates/>
    </xsl:template>
    
    <xsl:template match="akn:num[parent::akn:article] | akn:num[parent::akn:point]">
        <fo:block start-indent="0pt" space-after="8pt"
            line-height="14pt" hyphenate="false" font-size="12.5pt" 
            keep-with-next="always"
            font-weight="normal"
            font-style="normal">
            
            <fo:inline>
            <xsl:choose>
                <xsl:when test="ancestor::akn:quotedStructure">
                    <xsl:attribute name="font-weight">normal</xsl:attribute>
                    <xsl:attribute name="font-style">italic</xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:attribute name="font-weight">bold</xsl:attribute>
                    <xsl:attribute name="font-style">normal</xsl:attribute>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:apply-templates/>
            </fo:inline>
            
            <fo:inline padding-left="30px" font-weight="normal">
                <xsl:choose>
                    <xsl:when test="ancestor::akn:quotedStructure and parent::akn:point">
                        <xsl:attribute name="font-style">italic</xsl:attribute>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:attribute name="font-style">normal</xsl:attribute>
                    </xsl:otherwise>
                </xsl:choose>
            <xsl:apply-templates select="following-sibling::*[1][name()='heading']/* | following-sibling::*[1][name()='heading']/text()"/>
            </fo:inline>
        </fo:block>
    </xsl:template>
  
  
    <!-- ============================================== -->
    <!--                modifications                   -->
    <!-- ============================================== -->
    <xsl:template match="akn:quotedStructure">
        <fo:block-container>
            <xsl:attribute name="margin-top">
            <xsl:choose>
                <xsl:when test="preceding-sibling::akn:ref">14px</xsl:when>
                <xsl:otherwise>20px</xsl:otherwise>
            </xsl:choose>
            </xsl:attribute>
            
            <xsl:apply-templates/>
        </fo:block-container>
    </xsl:template>
    
    <!-- TODO: just a patch, find a better markup for this case -->
    <xsl:template match="akn:ref[parent::akn:mod][following-sibling::akn:quotedStructure][count(following-sibling::akn:*) = 1]">
        <fo:block font-style="italic" margin-bottom="4px" margin-top="20px">
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>
    
    
    
    <!-- ============================================== -->
    <!--                    Headings                    -->
    <!-- ============================================== -->
    <xsl:template match="akn:heading[parent::akn:article or parent::akn:point][preceding-sibling::akn:*[1][name()='num']]"/>
    
   
    <xsl:template match="akn:heading[parent::akn:hcontainer[not(contains(@name,'esito'))]]">
        <fo:block font-weight="bold" font-size="14px" margin-bottom="20px">
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>
    
    <xsl:template match="akn:heading">
        <fo:block font-style="italic" margin-bottom="6px">
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>
        
    
    <!-- ================================================== -->
    <!--                        alinea                      -->
    <!-- ================================================== --> 
    <xsl:template match="akn:alinea[preceding-sibling::akn:alinea]"/>
    
    <xsl:template match="akn:alinea">
    <fo:list-block margin-left="18px">
        <xsl:apply-templates select=". | following-sibling::akn:alinea" mode="inalinea"/>
    </fo:list-block>
    </xsl:template>
    
    <xsl:template match="akn:alinea" mode="inalinea">
    <fo:list-item space-after="8pt">
        <fo:list-item-label end-indent="label-end()">
            <fo:block text-align="justify" line-height="12.5pt" margin-left="0px"><xsl:value-of select="akn:num"/></fo:block>
        </fo:list-item-label>
        <fo:list-item-body start-indent="body-start()">
            <xsl:apply-templates select="akn:content"/>
        </fo:list-item-body>
    </fo:list-item>
    </xsl:template>
    
    <xsl:template match="akn:alinea[not(akn:num)][akn:content/akn:p[@status='omissis'] and (count(akn:content/*)=1)]" mode="inalinea">
        <fo:list-item space-after="8pt">
            <fo:list-item-label end-indent="label-end()">
                <fo:block text-align="justify" line-height="12.5pt" margin-left="0px">...</fo:block>
            </fo:list-item-label>
            <fo:list-item-body start-indent="body-start()">
                <fo:block/>
            </fo:list-item-body>
        </fo:list-item>
    </xsl:template>
    
    <!-- ================================================== -->
    <!--     Paragraphs/Subparagraphs (in Articles)         -->
    <!-- ================================================== -->   
    <xsl:template match="akn:num[parent::akn:paragraph or parent::akn:subparagraph]"/>
    
    <xsl:template match="akn:paragraph | akn:subparagraph">
        
        <xsl:choose>
            <xsl:when test="akn:alinea | akn:indent">
                <xsl:apply-templates select="akn:alinea/akn:content | akn:indent"/>
            </xsl:when>
            <xsl:when test="not(akn:subparagraph) and not(akn:content/akn:blockList)">
                <fo:block start-indent="0pt" space-after="8pt"
                    line-height="14pt" hyphenate="false" font-size="12.5pt">
                    
                    <fo:inline vertical-align="top" font-size="7px" font-style="normal"><xsl:value-of select="akn:num"/> </fo:inline>
                    <xsl:text> </xsl:text>
                <xsl:apply-templates select="akn:content/akn:p[position() = 1]/* | akn:content/akn:p[position() = 1]/text()"/>
                </fo:block>
                <xsl:apply-templates select="akn:content/akn:p[position() &gt; 1]"/>
         </xsl:when>
         <xsl:otherwise>
             <fo:block start-indent="0pt" space-after="8pt"
                 line-height="14pt" hyphenate="false" font-size="12.5pt" 
                 keep-with-next="always"
                 font-weight="normal"
                 font-style="italic" keep-with-next.within-page="always">
                 <fo:inline padding-right="5px"><xsl:apply-templates select="akn:num/* | akn:num/text()"/></fo:inline>
                 <fo:inline><xsl:apply-templates select="akn:heading/* | akn:heading/text()"/></fo:inline>
             </fo:block>
             <xsl:apply-templates select="akn:*[not(name() = 'num') and not(name() = 'heading')]"/>
         </xsl:otherwise>   
        </xsl:choose>
        
    </xsl:template>
    
    
    <!-- ============================================== -->
    <!--                 containers                     -->
    <!-- ============================================== -->
    <xsl:template match="akn:container[@class='compendio']">
        <fo:block-container font-style="italic">
            <xsl:apply-templates/>
        </fo:block-container>
    </xsl:template>

    <!-- ============================================== -->
    <!--              hContainers/Parts                 -->
    <!-- ============================================== -->
    <xsl:template match="akn:hcontainer">
        <fo:block-container keep-together="always" space-before="24px" >
            <xsl:apply-templates/>
        </fo:block-container>
    </xsl:template>
    
    <xsl:template match="akn:num[parent::akn:hcontainer]">
        <fo:block start-indent="0pt" space-after="8pt"
            line-height="14pt" hyphenate="false" font-size="12.5pt" 
            font-weight="normal">
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>
    
    <!-- ============================================== -->
    <!--                    Lists                       -->
    <!-- ============================================== -->
    <xsl:template match="akn:listIntroduction">
        <fo:block start-indent="0pt" space-after="8pt"
            line-height="14pt" hyphenate="false" font-size="12.5pt" 
            language="en" country="US">
            <xsl:if test="contains(@class,'italic')">
                <xsl:attribute name="font-style">italic</xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>
    
    <xsl:template match="akn:blockList[.//akn:item//akn:num]">
        <fo:list-block space-before="10pt" space-after="10pt"
            provisional-distance-between-starts="85pt" hyphenate="false">
        <xsl:apply-templates select="akn:listIntroduction"/>
        <xsl:for-each select="akn:item">
            <fo:list-item space-after="8pt">
                <fo:list-item-label end-indent="label-end()">
                    <fo:block text-align="justify" line-height="12.5pt" margin-left="0px"><xsl:value-of select="akn:num"/></fo:block>
                </fo:list-item-label>
                <fo:list-item-body start-indent="body-start()">
                    <xsl:for-each select="akn:p">
                        <fo:block  line-height="12.5pt"><xsl:apply-templates/></fo:block>  
                    </xsl:for-each>
                </fo:list-item-body>
            </fo:list-item>
        </xsl:for-each>
        </fo:list-block>
    </xsl:template>
    
        
    <xsl:template match="akn:p[@class='line'][parent::akn:item] | akn:p[ancestor::akn:indent]">
        <fo:list-block space-before="14pt" space-after="10pt"
            provisional-distance-between-starts="45pt" hyphenate="false">
            <fo:list-item>
                <fo:list-item-label end-indent="label-end()">
                    <fo:block text-align="justify" line-height="14pt" margin-left="15px">–</fo:block>
                </fo:list-item-label>
                <fo:list-item-body start-indent="body-start()">
                    <fo:block  line-height="14pt" start-indent="35pt"><xsl:apply-templates/></fo:block>
                </fo:list-item-body>
            </fo:list-item>
        </fo:list-block>
        
    </xsl:template>
    
    
    <!-- ============================================== -->
    <!--                    Tables                      -->
    <!-- ============================================== -->
    <xsl:variable name="tWidth">
        <xsl:choose>
            <xsl:when test="//akn:doc[@name='allegato']">680</xsl:when>
            <xsl:otherwise>436</xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    
    <xsl:template match="akn:table">
        <xsl:apply-templates select="akn:caption"/>
        <fo:table border-collapse="collapse" table-layout="fixed" font-size="11px" width="{$tWidth}px"
            border-top="1px solid black" border-bottom="1px solid black">
            
            <xsl:apply-templates select="akn:tr[akn:th][not(akn:th[@colspan])]" mode="countColumns"/>
            
            <fo:table-body>
                <xsl:apply-templates select="akn:tr"/>    
            </fo:table-body>
        </fo:table>
        
        <!-- Patch: FOP0.95 does not support correctly footnotes in table. Fake foonotes added after the table. -->
        <xsl:apply-templates select=".//akn:authorialNote" mode="patchFootnotesInTable"/>
        
    </xsl:template>
    
    <xsl:template match="akn:tr[akn:th][not(akn:th[@colspan])]" mode="countColumns">
        <xsl:variable name="tCols" select="count(akn:th)"/>
        
        <xsl:for-each select="akn:th">
            <xsl:variable name="cWidth"><xsl:value-of select="$tWidth div $tCols"/>px</xsl:variable>
            <fo:table-column column-number="{position()}" column-width="{$cWidth}"/>
        </xsl:for-each>
    </xsl:template>
    
    <xsl:template match="akn:tr">
        <fo:table-row>
            <xsl:apply-templates/>
        </fo:table-row>
    </xsl:template>
    
    <xsl:template match="akn:th | akn:td">
        <fo:table-cell padding-left="3px" >
            
                <xsl:choose>
                    <xsl:when test="ancestor::akn:doc[@name='allegato']">
                        <xsl:attribute name="padding-top">0px</xsl:attribute>
                        <xsl:attribute name="padding-bottom">0px</xsl:attribute>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:attribute name="padding-top">3px</xsl:attribute>
                        <xsl:attribute name="padding-bottom">3px</xsl:attribute>
                    </xsl:otherwise>
                </xsl:choose>
            
            
            
                <xsl:choose>
                    <xsl:when test="parent::akn:tr[contains(@class,'border') and not(contains(@class,'border-'))]">
                        <xsl:attribute name="border">1px solid black</xsl:attribute>
                    </xsl:when>
                    <xsl:otherwise>
                         <xsl:if test="parent::akn:tr[contains(@class,'border-bottom')]">
                            <xsl:attribute name="border-bottom">1px solid black</xsl:attribute>
                         </xsl:if>
                         <xsl:if test="parent::akn:tr[contains(@class,'border-top')]">
                            <xsl:attribute name="border-top">1px solid black</xsl:attribute>
                         </xsl:if>
                        <xsl:if test="parent::akn:tr[contains(@class,'border-left')]">
                            <xsl:attribute name="border-left">1px solid black</xsl:attribute>
                        </xsl:if>
                        <xsl:if test="parent::akn:tr[contains(@class,'border-right')]">
                            <xsl:attribute name="border-right">1px solid black</xsl:attribute>
                        </xsl:if>
                        <xsl:if test="contains(@class,'border-bottom')">
                            <xsl:attribute name="border-bottom">1px solid black</xsl:attribute>
                        </xsl:if>
                        <xsl:if test="contains(@class,'border-top')">
                            <xsl:attribute name="border-top">1px solid black</xsl:attribute>
                        </xsl:if>
                        <xsl:if test="contains(@class,'border-left')">
                            <xsl:attribute name="border-left">1px solid black</xsl:attribute>
                        </xsl:if>
                        <xsl:if test="contains(@class,'border-right')">
                            <xsl:attribute name="border-right">1px solid black</xsl:attribute>
                        </xsl:if>                        
                    </xsl:otherwise>                
                </xsl:choose>

                <xsl:if test="ancestor::akn:table[contains(@class,'border-columns')]">
                    <xsl:attribute name="border-left">1px solid black</xsl:attribute>
                    <xsl:if test="not(following-sibling::akn:td or following-sibling::akn:th)">
                        <xsl:attribute name="border-right">1px solid black</xsl:attribute>
                    </xsl:if>
                </xsl:if>
            
                <xsl:choose>
                    <xsl:when test="parent::akn:tr[contains(@class,'bigger')] or contains(@class,'bigger')">
                        <xsl:attribute name="font-size">120%</xsl:attribute>
                    </xsl:when>
                    <xsl:when test="parent::akn:tr[contains(@class,'smaller')] or contains(@class,'smaller')">
                        <xsl:attribute name="font-size">80%</xsl:attribute>
                    </xsl:when>
                </xsl:choose>
            
            
            <xsl:apply-templates select="@colspan | @rowspan"/>
            
            <xsl:apply-templates/>
        </fo:table-cell>
    </xsl:template>        
    
    <xsl:template match="@colspan">
        <xsl:attribute name="number-columns-spanned"><xsl:value-of select="."/></xsl:attribute>
    </xsl:template>
    
    <xsl:template match="@rowspan">
        <xsl:attribute name="number-rows-spanned"><xsl:value-of select="."/></xsl:attribute>
    </xsl:template>
    
    <xsl:template match="akn:caption">
        <fo:block-container margin-top="12px">
            <fo:block text-transform="none" text-align="left"  line-height="14pt" hyphenate="false" font-weight="bold" font-style="normal"
                space-after="22pt" font-size="14px" margin-right="60px">
                    <xsl:apply-templates/>
            </fo:block>
            <xsl:if test="ancestor::akn:doc[@name='allegato']">
            <fo:block-container position="absolute" left="630px">
                <fo:block text-transform="none" text-align="left"  line-height="14pt" hyphenate="false" 
                    font-weight="normal" font-style="italic"
                    space-after="22pt" font-size="12px">
                    <xsl:apply-templates select="//akn:docTitle"/>
                </fo:block>
            </fo:block-container>
            </xsl:if>
        </fo:block-container>
    </xsl:template>
    
    <!-- ============================================== -->
    <!--                Paragraphs/Blocks               -->
    <!-- ============================================== -->
    <xsl:template match="akn:p[ancestor::akn:alinea/ancestor::akn:paragraph]">
        <fo:block start-indent="0pt" space-after="8pt"
            line-height="14pt" hyphenate="false" font-size="12.5pt">
            
            <fo:inline vertical-align="top" font-size="7px" font-style="normal"><xsl:value-of select="count(ancestor::akn:paragraph/preceding-sibling::akn:paragraph) + 1"/></fo:inline>
            <xsl:text> </xsl:text>
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>
    
    
    <xsl:template match="akn:p[@class='addressee']">
        <fo:block start-indent="230pt" space-after="28pt" line-stacking-strategy="font-height"
            line-height="14pt" hyphenate="false" font-size="12.5pt" 
            language="en" country="US" text-align="left" >
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>
    
    <xsl:template match="akn:br">
        <fo:block>
            <xsl:if test="contains(@class,'double')">
                <xsl:attribute name="margin-top">16px</xsl:attribute>
            </xsl:if>
        </fo:block>
    </xsl:template>
    
    <xsl:template match="akn:p[ancestor::akn:conclusions][*[1][local-name()='date']]">
        <fo:block start-indent="0pt" space-after="6pt" space-before="40pt" 
            line-height="17pt" hyphenate="false" font-size="12.5pt" 
            language="en" country="US" text-align-last="justify" text-align="justify">
        <xsl:apply-templates/>
        </fo:block>
    </xsl:template>
    
    <xsl:template match="akn:date[parent::akn:p[ancestor::akn:conclusions][*[1][local-name()='date']]]">
        <fo:inline><xsl:apply-templates/></fo:inline>
        <fo:leader leader-pattern="space"/>
    </xsl:template>
    
    <xsl:template match="akn:p[@class='bottomOfPage']"/>
        
    
    <xsl:template match="akn:p[akn:date or akn:location][following-sibling::akn:*[1][@class='addresser']]"/>
    
    <xsl:template match="akn:p[@class='addresser']">
        <fo:block-container>
        <fo:block start-indent="0pt" space-after="10pt"
            line-height="14pt" hyphenate="false" 
            language="en" country="US" font-size="12.5pt" text-align="justify" margin-right="250pt">
            <xsl:apply-templates/>
        </fo:block>
            <xsl:if test="preceding-sibling::akn:*[1][name()='p'][akn:date or akn:location]">
            <fo:block-container position="absolute" left="230pt">
                <fo:block start-indent="0pt" space-after="10pt"
                    line-height="14pt" hyphenate="false" font-size="12.5pt" text-align="justify">
                <xsl:apply-templates select="preceding-sibling::akn:p[1]/node()"/>
                </fo:block>    
            </fo:block-container>
            </xsl:if>
        </fo:block-container>    
    </xsl:template>    
        
        
    <xsl:template match="akn:p">
        <fo:block 
            line-height="14pt" hyphenate="false" 
            language="en" country="US">
            
            <xsl:choose>
                <xsl:when test="not(ancestor::akn:alinea)">
                    <xsl:attribute name="start-indent">0pt</xsl:attribute>
                </xsl:when>
                <xsl:otherwise></xsl:otherwise>
            </xsl:choose>
            
            
            <xsl:attribute name="space-after">
                <xsl:choose>
                    <xsl:when test="ancestor::akn:blockList/ancestor::akn:preamble">0pt</xsl:when>
                    <xsl:when test="ancestor::akn:authorialNote">2pt</xsl:when>
                    <xsl:otherwise>10pt</xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
            
            
            
            <xsl:if test="not(ancestor::akn:table)">
            <xsl:attribute name="font-size">
                <xsl:choose>
                    <xsl:when test="contains(@class,'smaller')">11.5pt</xsl:when>
                    <xsl:otherwise>12.5pt</xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
            </xsl:if>
            
            <xsl:if test="contains(@class,'italic')">
                <xsl:attribute name="font-style">italic</xsl:attribute>
            </xsl:if>
            
            <xsl:attribute name="text-align">
            <xsl:choose>
                <xsl:when test="contains(@class,'right')">right</xsl:when>
                <xsl:when test="ancestor::akn:td[contains(@class,'right') and not(contains(@class,'border-right'))]">right</xsl:when>
                <xsl:when test="ancestor::akn:th[contains(@class,'right') and not(contains(@class,'border-right'))]">right</xsl:when>
                <xsl:when test="ancestor::akn:th[@class='right']">right</xsl:when>
                <xsl:when test="ancestor::akn:td[@class='right']">right</xsl:when>
                <xsl:when test="ancestor::akn:table">left</xsl:when>
                <xsl:otherwise>justify</xsl:otherwise>
            </xsl:choose>
            </xsl:attribute>
            
            
            <xsl:choose>
                <xsl:when test="(count(akn:*) = 2) and akn:span[contains(@class,'left')] and akn:span[contains(@class,'right')]">
                    
                    <xsl:variable name="percLeft">
                        <xsl:choose>
                            <xsl:when test="akn:span[contains(@class,'right-long')]">25%</xsl:when>
                            <xsl:otherwise>50%</xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    <xsl:variable name="percRight">
                        <xsl:choose>
                            <xsl:when test="akn:span[contains(@class,'right-long')]">75%</xsl:when>
                            <xsl:otherwise>50%</xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    <xsl:variable name="rightPosition">
                        <xsl:choose>
                            <xsl:when test="akn:span[contains(@class,'right-long')]">110px</xsl:when>
                            <xsl:otherwise>230px</xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    
                    
                    
                    <fo:block-container>
                        <fo:block-container position="absolute" width="{$percLeft}">
                            <fo:block>
                                <xsl:apply-templates select="akn:span[contains(@class,'left')]"/>    
                            </fo:block>
                        </fo:block-container>
                        <fo:block-container position="absolute" width="{$percRight}" left="{$rightPosition}">
                            <fo:block>
                                <xsl:apply-templates select="akn:span[contains(@class,'right')]"/>    
                            </fo:block>
                        </fo:block-container>
                    </fo:block-container>
                    
                </xsl:when>
                <xsl:when test="@status='omissis'">
                    ...
                </xsl:when>
                <xsl:otherwise><xsl:apply-templates/></xsl:otherwise>
            </xsl:choose>
            
            
        </fo:block>
    </xsl:template>
    
    <!-- ============================================== -->
    <!--                    Formula                     -->
    <!-- ============================================== -->  
    <xsl:template match="akn:formula">
        <fo:block-container margin-bottom="24px">
            <xsl:choose>
                <xsl:when test="contains(@class,'italic')">
                    <xsl:attribute name="font-style">italic</xsl:attribute>
                </xsl:when>
            </xsl:choose>
            <xsl:apply-templates/>
        </fo:block-container>
    </xsl:template>
    
    
    <!-- ============================================== -->
    <!--                  Conclusions                   -->
    <!-- ============================================== -->  
    <xsl:template match="akn:conclusions">
        <fo:block-container margin-top="30px">
            <xsl:apply-templates/>
        </fo:block-container>
    </xsl:template>
    
    <!-- ============================================== -->
    <!--                    Signature                   -->
    <!-- ============================================== -->
    <xsl:template match="akn:p[akn:signature][not(preceding-sibling::akn:p[akn:signature])]">
    <fo:block-container margin-top="25px">
        <xsl:apply-templates select=". | following-sibling::akn:p[akn:signature]" mode="signature-block"/>
    </fo:block-container>
    </xsl:template>
    
    <xsl:template match="akn:p[akn:signature][preceding-sibling::akn:p[akn:signature]]"/>
    
    
    <xsl:template match="akn:p[akn:signature]" mode="signature-block">
        
        <xsl:variable name="perc">
            <xsl:choose>
                <xsl:when test="akn:signature[akn:span[contains(@class,'right-long')]]">75%</xsl:when>
                <xsl:otherwise>50%</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="rightPosition">
            <xsl:choose>
                <xsl:when test="akn:signature[akn:span[contains(@class,'right-long')]]">110px</xsl:when>
                <xsl:when test="akn:signature[akn:span[contains(@class,'right')]]">230px</xsl:when>
                <xsl:otherwise>0px</xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        
        <fo:block-container position="absolute" width="{$perc}">
            <xsl:attribute name="left"><xsl:value-of select="$rightPosition"/></xsl:attribute>
            
            <xsl:for-each select="akn:signature">
            <fo:block start-indent="0pt" space-after="0pt" line-height="14pt" hyphenate="false"
                font-size="12.5pt" text-align="left">
                <xsl:apply-templates/>    
            </fo:block>
            </xsl:for-each>
        </fo:block-container>
    </xsl:template>
    

    
    <!-- ============================================== -->
    <!--            Authorial Note / Footnote           -->
    <!-- ============================================== -->   
    <xsl:template match="akn:authorialNote">
        
        <xsl:choose>
            <xsl:when test="ancestor::akn:table">
                <fo:inline vertical-align="top" font-size="7px" font-style="normal">
                    <xsl:value-of select="@marker"/></fo:inline>
            </xsl:when>
            <xsl:otherwise>
                <fo:footnote font-weight="normal">
                    <fo:inline vertical-align="top" font-size="7px" font-style="normal">
                        <xsl:value-of select="@marker"/></fo:inline>
                    <fo:footnote-body>
                        <xsl:apply-templates/>
                    </fo:footnote-body>
                </fo:footnote>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <xsl:template match="akn:authorialNote" mode="patchFootnotesInTable">
        <fo:block>
        <fo:footnote>
            <fo:inline/>
            <fo:footnote-body>
                <xsl:apply-templates/>
            </fo:footnote-body>
        </fo:footnote>
        </fo:block>     
    </xsl:template>
  
  
    <xsl:template match="akn:p[parent::akn:authorialNote]">
    <fo:list-block space-before="0pt" space-after="0pt"
        provisional-distance-between-starts="25pt" hyphenate="false" margin-top="0pt" margin-bottom="0pt">
        <fo:list-item>
            <xsl:attribute name="margin-bottom">
                <xsl:choose>
                    <xsl:when test="following-sibling::akn:p">0px</xsl:when>
                    <xsl:otherwise>1pt</xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
            <fo:list-item-label end-indent="label-end()">
                <fo:block text-align="justify" line-height="14pt" >
                    <fo:inline vertical-align="top" font-size="9px" font-style="normal">
                            <xsl:if test="not(preceding-sibling::akn:p)">
                                <xsl:value-of select="parent::akn:authorialNote/@marker"/>
                            </xsl:if>
                    </fo:inline>
                </fo:block>
            </fo:list-item-label>
            <fo:list-item-body start-indent="body-start()">
                <fo:block line-height="11.5pt" hyphenate="false" font-size="11.5pt" font-style="normal"
                    language="en" country="US" text-align="justify">
                    
                    <xsl:if test="parent::akn:authorialNote/@marker=''">
                        <xsl:attribute name="start-indent">0pt</xsl:attribute>
                    </xsl:if>    
                    <xsl:apply-templates/>
                </fo:block>
            </fo:list-item-body>
        </fo:list-item>
    </fo:list-block>
    </xsl:template>
    
  <!-- 
    <xsl:template match="akn:p[parent::akn:authorialNote]">
        <fo:block start-indent="0pt"
            line-height="11.5pt" hyphenate="false" font-size="11.5pt" font-style="normal"
            language="en" country="US" text-align="left">
            <fo:inline vertical-align="top" font-size="7px" font-style="normal">
              
                
                <xsl:if test="not(preceding-sibling::akn:p)">
                    <xsl:value-of select="parent::akn:authorialNote/@marker"/>
                </xsl:if>
            </fo:inline> 
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>
  -->
   
    
    <!-- ============================================== -->
    <!--                    Inline                      -->
    <!-- ============================================== -->
    <xsl:template match="akn:span[@class='bigger']">
        <fo:inline font-size="120%">
            <xsl:apply-templates/>
        </fo:inline>
        <xsl:if test="parent::akn:docTitle">
            <fo:block space-after="5pt"/>
        </xsl:if>
    </xsl:template>

    <xsl:template match="akn:span[@class='smaller']">
        <fo:inline font-size="80%">
            <xsl:apply-templates/>
        </fo:inline>
    </xsl:template>
    
    <xsl:template match="akn:span[@class='italic']">
        <fo:inline font-style="italic">
            <xsl:apply-templates/>
        </fo:inline>
    </xsl:template>

    <xsl:template match="akn:span[@class='bold']">
        <fo:inline font-weight="bold">
            <xsl:apply-templates/>
        </fo:inline>
    </xsl:template>
    
    <xsl:template match="akn:docIntroducer">
        <fo:inline>
            <xsl:choose>
                <xsl:when test="@class='italic'">
                    <xsl:attribute name="font-style">italic</xsl:attribute>
                </xsl:when>
                <xsl:otherwise/>
            </xsl:choose>            
            <xsl:apply-templates/>
        </fo:inline>
    </xsl:template>
    
    <!-- ============================================== -->
    <!--                    Default                     -->
    <!-- ============================================== -->
    <xsl:template match="akn:*">
        <xsl:apply-templates/>    
    </xsl:template>
    
    <xsl:template match="text()">
        <xsl:copy-of select="."/>
    </xsl:template>

</xsl:stylesheet>
