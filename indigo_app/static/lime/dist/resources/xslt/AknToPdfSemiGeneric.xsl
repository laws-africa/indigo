<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" 
    xmlns:fo="http://www.w3.org/1999/XSL/Format">
    <xsl:param name="startPageNumber">1</xsl:param>
    
    <xsl:template match="/">
        <fo:root xmlns:fo="http://www.w3.org/1999/XSL/Format">
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
                        margin-bottom="66.67pt"/>
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
            </fo:layout-master-set>
            
           <xsl:apply-templates/>
        </fo:root>
    </xsl:template>
  
    <xsl:template match="akn:doc | akn:bill | akn:act">
        <fo:page-sequence format="1" master-reference="all-pages" initial-page-number="{$startPageNumber}">
            <!-- TODO: use fo:block-container (absolute position) instead of tables?does FOP support it? -->
            <fo:static-content flow-name="first-page-xsl-region-before">
                <fo:block></fo:block>
            </fo:static-content>
            <fo:static-content flow-name="first-page-xsl-region-after">
                <fo:block  xsl:use-attribute-sets="pageNumber">
                    <fo:inline><xsl:apply-templates select="//akn:docketNumber"/></fo:inline>
                    <fo:leader leader-pattern="space"/>
                    <fo:page-number/>
                </fo:block>
            </fo:static-content>
            <fo:static-content flow-name="odd-xsl-region-before">
                <fo:table>
                    <fo:table-column/>
                    <fo:table-column/>
                    <fo:table-body>
                        <fo:table-row>
                            <fo:table-cell>
                                <fo:block>
                                </fo:block>
                            </fo:table-cell>
                            <fo:table-cell>
                                <fo:block>
                                </fo:block>
                            </fo:table-cell>
                        </fo:table-row>
                    </fo:table-body>
                </fo:table>
            </fo:static-content>
            <fo:static-content flow-name="odd-xsl-region-after">
                <fo:block  xsl:use-attribute-sets="pageNumber">
                    <fo:page-number/>
                </fo:block>
            </fo:static-content>
            <fo:static-content flow-name="even-xsl-region-before">
                <fo:table>
                    <fo:table-column/>
                    <fo:table-column/>
                    <fo:table-body>
                        <fo:table-row>
                            <fo:table-cell>
                                <fo:block>
                                </fo:block>
                            </fo:table-cell>
                            <fo:table-cell>
                                <fo:block>
                                </fo:block>
                            </fo:table-cell>
                        </fo:table-row>
                    </fo:table-body>
                </fo:table>
            </fo:static-content>
            <fo:static-content flow-name="even-xsl-region-after">
                <fo:block  xsl:use-attribute-sets="pageNumber">
                    <fo:page-number/>
                </fo:block>
            </fo:static-content>
            <fo:static-content flow-name="xsl-footnote-separator">
                <fo:block>x</fo:block>
            </fo:static-content>
            <fo:flow widows="2" orphans="2"
                flow-name="xsl-region-body">
                <xsl:choose>
                    <xsl:when test=".//akn:p"><xsl:apply-templates select="akn:*"/></xsl:when>
                    <xsl:otherwise>
                        <fo:block>
                            EMPTY DOCUMENT.
                        </fo:block> 
                    </xsl:otherwise>
                </xsl:choose>
            </fo:flow>
        </fo:page-sequence>     
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
        <fo:block-container>
            <xsl:apply-templates/>
        </fo:block-container>       
    </xsl:template>
    
    <!-- docTitle (in paragraph) -->
    <xsl:template match="akn:p[akn:docTitle]">
        <fo:block>
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>
    
    <!-- docNumber (in paragraph) -->
    <xsl:template match="akn:p[akn:docNumber]">
        <fo:block>
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>

    <!-- ============================================== -->
    <!--                    Chapter                     -->
    <!-- ============================================== -->
    <!-- TODO: use this approach also for article/point and al other hcontainer(s) -->
    <xsl:template match="akn:chapter | akn:subchapter">
        <fo:block  hyphenate="false" keep-with-next="always" keep-with-next.within-page="always">
            <fo:inline>               
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
        <fo:block hyphenate="false" keep-with-next="always">
            <fo:inline xsl:use-attribute-sets="num">
            <xsl:apply-templates/>
            </fo:inline>
            <fo:inline>
            <xsl:apply-templates select="following-sibling::*[1][name()='heading']/* | following-sibling::*[1][name()='heading']/text()"/>
            </fo:inline>
        </fo:block>
    </xsl:template>
  
  
    <!-- ============================================== -->
    <!--                modifications                   -->
    <!-- ============================================== -->
    <xsl:template match="akn:quotedStructure">
        <fo:block-container>           
            <xsl:apply-templates/>
        </fo:block-container>
    </xsl:template>
    
    <!-- ============================================== -->
    <!--                    Headings                    -->
    <!-- ============================================== -->
    <xsl:template match="akn:heading">
        <fo:block>
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>
    
    <!-- ================================================== -->
    <!--                        alinea                      -->
    <!-- ================================================== --> 
    <xsl:template match="akn:alinea[preceding-sibling::akn:alinea]"/>
    
    <xsl:template match="akn:alinea">
    <fo:list-block>
        <xsl:apply-templates select=". | following-sibling::akn:alinea" mode="inalinea"/>
    </fo:list-block>
    </xsl:template>
    
    <xsl:template match="akn:alinea" mode="inalinea">
    <fo:list-item>
        <fo:list-item-label end-indent="label-end()">
            <fo:block><xsl:value-of select="akn:num"/></fo:block>
        </fo:list-item-label>
        <fo:list-item-body start-indent="body-start()">
            <xsl:apply-templates select="akn:content"/>
        </fo:list-item-body>
    </fo:list-item>
    </xsl:template>
    
    <xsl:template match="akn:alinea[not(akn:num)][akn:content/akn:p[@status='omissis'] and (count(akn:content/*)=1)]" mode="inalinea">
        <fo:list-item>
            <fo:list-item-label end-indent="label-end()">
                <fo:block>...</fo:block>
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
                <fo:block hyphenate="false">
                    <fo:inline><xsl:value-of select="akn:num"/> </fo:inline>
                    <xsl:text> </xsl:text>
                <xsl:apply-templates select="akn:content/akn:p[position() = 1]/* | akn:content/akn:p[position() = 1]/text()"/>
                </fo:block>
                <xsl:apply-templates select="akn:content/akn:p[position() &gt; 1]"/>
         </xsl:when>
         <xsl:otherwise>
             <fo:block hyphenate="false"  keep-with-next="always" keep-with-next.within-page="always">
                 <fo:inline><xsl:apply-templates select="akn:num/* | akn:num/text()"/></fo:inline>
                 <fo:inline><xsl:apply-templates select="akn:heading/* | akn:heading/text()"/></fo:inline>
             </fo:block>
             <xsl:apply-templates select="akn:*[not(name() = 'num') and not(name() = 'heading')]"/>
         </xsl:otherwise>   
        </xsl:choose>
        
    </xsl:template>

    <!-- ============================================== -->
    <!--              hContainers/Parts                 -->
    <!-- ============================================== -->
    <xsl:template match="akn:hcontainer">
        <fo:block-container keep-together="always">
            <xsl:apply-templates/>
        </fo:block-container>
    </xsl:template>
    
    <xsl:template match="akn:num[parent::akn:hcontainer]">
        <fo:block hyphenate="false">
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>
    
    <!-- ============================================== -->
    <!--                    Lists                       -->
    <!-- ============================================== -->
    <xsl:template match="akn:listIntroduction">
        <fo:block  hyphenate="false">
            <xsl:if test="contains(@class,'italic')">
                <xsl:attribute name="font-style">italic</xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>
    
    <xsl:template match="akn:blockList[.//akn:item//akn:num]">
        <fo:list-block hyphenate="false">
        <xsl:apply-templates select="akn:listIntroduction"/>
        <xsl:for-each select="akn:item">
            <fo:list-item>
                <fo:list-item-label end-indent="label-end()">
                    <fo:block><xsl:value-of select="akn:num"/></fo:block>
                </fo:list-item-label>
                <fo:list-item-body start-indent="body-start()">
                    <xsl:for-each select="akn:p">
                        <fo:block><xsl:apply-templates/></fo:block>  
                    </xsl:for-each>
                </fo:list-item-body>
            </fo:list-item>
        </xsl:for-each>
        </fo:list-block>
    </xsl:template>
    
    <!-- ============================================== -->
    <!--                    Tables                      -->
    <!-- ============================================== -->   
    <xsl:template match="akn:table">
        <xsl:apply-templates select="akn:caption"/>
        <fo:table table-layout="fixed">
            
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
        <fo:table-cell >     
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
        
    <!-- ============================================== -->
    <!--                Paragraphs/Blocks               -->
    <!-- ============================================== -->
      
    <xsl:template match="akn:br">
        <fo:block/>
    </xsl:template>
    
    <xsl:template match="akn:date[parent::akn:p[ancestor::akn:conclusions][*[1][local-name()='date']]]">
        <fo:inline><xsl:apply-templates/></fo:inline>
        <fo:leader leader-pattern="space"/>
    </xsl:template>
             
    <xsl:template match="akn:p">
        <fo:block>
            <xsl:choose>
                <xsl:when test="not(ancestor::akn:alinea)">
                    <xsl:attribute name="start-indent">0pt</xsl:attribute>
                </xsl:when>
                <xsl:otherwise></xsl:otherwise>
            </xsl:choose>
         
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
        <fo:block-container>
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
        <fo:block-container>
            <xsl:apply-templates/>
        </fo:block-container>
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
