<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:html="http://www.w3.org/1999/xhtml"
    xmlns="http://www.akomantoso.org/2.0"
    xmlns:xml="http://www.w3.org/XML/1998/namespace"
    exclude-result-prefixes="xs"
    version="1.0">
    <xsl:output method="xml" indent="yes" encoding="UTF-8" />
    
    <xsl:template match="/">
    	<akomaNtoso>
        	<xsl:apply-templates />
		</akomaNtoso>
    </xsl:template>
	
    <xsl:template mode="aknPrefixAttributes" match="@*" >
    	<xsl:variable name="attName"><xsl:value-of select="substring-after(name(.),'_')"/></xsl:variable>
        <xsl:choose>
            <xsl:when test="substring-before(name(.),'_') = 'akn'">
               <xsl:attribute name="{$attName}"><xsl:value-of select="." /></xsl:attribute>
            </xsl:when>
            <xsl:when test="name(.) = 'alternativeto' or
                        name(.) = 'name' or
                        name(.) = 'number' or
                        name(.) = 'source' or
                        name(.) = 'date' or
                        name(.) = 'time' or
                        name(.) = 'href' or
                        name(.) = 'value' or
                        name(.) = 'by' or
                        name(.) = 'as' or
                        name(.) = 'starttime' or
                        name(.) = 'endtime' or
                        name(.) = 'to' or
                        name(.) = 'choice' or
                        name(.) = 'showas' or
                        name(.) = 'shortform' or
                        name(.) = 'src' or
                        name(.) = 'alt' or
                        name(.) = 'period' or
                        name(.) = 'status' or
                        name(.) = 'marker' or
                        name(.) = 'placement' or
                        name(.) = 'placementbase' or
                        name(.) = 'exclusion' or
                        name(.) = 'incomplete' or
                        name(.) = 'actor' or
                        name(.) = 'outcome' or
                        name(.) = 'startquote' or
                        name(.) = 'endquote' or
                        name(.) = 'rowspan' or
                        name(.) = 'colspan' or
                        name(.) = 'title' or
                        name(.) = 'eid' or
                        name(.) = 'wid' or
                        name(.) = 'guid' or
                        name(.) = 'refersto' or
                        name(.) = 'contains' or
                        name(.) = 'includedin' or
                        name(.) = 'level' or
                        name(.) = 'for' or
                        name(.) = 'empoweredby' or
                        name(.) = 'type' or
                        name(.) = 'normalized' or
                        name(.) = 'from' or
                        name(.) = 'upto' or
                        name(.) = 'originaltext' or
                        name(.) = 'width' or
                        name(.) = 'breakat' or
                        name(.) = 'target' or
                        name(.) = 'height' or
                        name(.) = 'border' or
                        name(.) = 'cellspacing' or
                        name(.) = 'cellpadding' or
                        name(.) = 'language' or
                        name(.) = 'fromlanguage' or
                        name(.) = 'authoritative' or
                        name(.) = 'pivot' or
                        name(.) = 'dictionary' or
                        name(.) = 'originatingexpression' or
                        name(.) = 'original' or
                        name(.) = 'current' or
                        name(.) = 'start' or
                        name(.) = 'end' or
                        name(.) = 'pos' or
                        name(.) = 'frozen' or
                        name(.) = 'duration'">
                <xsl:attribute name="{name(.)}"><xsl:value-of select="." /></xsl:attribute>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    
    <xsl:template mode="notAknPrefixAttributes" match="@*" >
    	<xsl:if test="not(substring-before(name(.),'_') = 'akn')">
        	<xsl:attribute name="{name(.)}"><xsl:value-of select="." /></xsl:attribute>
        </xsl:if>	
    </xsl:template>
    
    <xsl:template mode="aknPrefixAttributesWithoutId" match="@*" >
    	<xsl:variable name="attName"><xsl:value-of select="substring-after(name(.),'_')"/></xsl:variable>
    	<xsl:if test="substring-before(name(.),'_') = 'akn' and $attName != 'id'">
			<xsl:attribute name="{$attName}"><xsl:value-of select="." /></xsl:attribute>
        </xsl:if>	
    </xsl:template>
    
    <xsl:template mode="allAttributes" match="@*" >
		<xsl:attribute name="{name(.)}"><xsl:value-of select="." /></xsl:attribute>
    </xsl:template>
    
	<xsl:template match="   div| 
    						span[@internalid]">
        <xsl:variable name="aknName">
            <xsl:if test="substring-after(./@class,' ') != ''">
                <xsl:value-of select="translate(substring-after(./@class,' '),'_','')" />
            </xsl:if>
            <xsl:if test="substring-after(./@class,' ') = ''">
                <xsl:value-of select="translate(@class,'_','')" />
            </xsl:if>
            <xsl:if test="./@class = ''">
            	<xsl:value-of select="name(.)" />
            </xsl:if>
        </xsl:variable>
        <xsl:choose>
        	<!-- Document root elements -->
		    <xsl:when test="$aknName='bill' or
		    				$aknName='act' or
		    				$aknName='doc' or
		    				$aknName='judgement' or
		    				$aknName='amendmentList' or
		    				$aknName='amendment' or 
		    				$aknName='debateReport' or 
		    				$aknName='officialGazette' or
		    				$aknName='debate'">
        	    <xsl:element name="{$aknName}">
		        	<xsl:apply-templates select="@*" mode="aknPrefixAttributes" />
		       		<xsl:apply-templates />
       			</xsl:element>
        	</xsl:when> 
        	<!-- All elements -->
		    <xsl:when test="$aknName != ''">
        	    <xsl:element name="{$aknName}">
		        	<xsl:apply-templates select="@*" mode="aknPrefixAttributes" />
		       		<xsl:apply-templates />
       			</xsl:element>
        	</xsl:when>
        	<xsl:otherwise>
        	   <xsl:apply-templates />
        	</xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <xsl:template match="div[contains(@class,'preface')] |
    					 div[contains(@class,'preamble')] |
    					 div[contains(@class,'conclusions')]">
		<xsl:variable name="aknName">
            <xsl:if test="substring-after(./@class,' ') != ''">
                <xsl:value-of select="translate(substring-after(./@class,' '),'_','')" />
            </xsl:if>
            <xsl:if test="substring-after(./@class,' ') = ''">
                <xsl:value-of select="translate(@class,'_','')" />
            </xsl:if>
            <xsl:if test="./@class = ''">
            	<xsl:value-of select="name(.)" />
            </xsl:if>
        </xsl:variable>
		<xsl:element name="{$aknName}">
			<xsl:apply-templates select="@*" mode="aknPrefixAttributes" />
			<xsl:call-template name="manageImplicitP" />
		</xsl:element>
	</xsl:template>
    
    <xsl:template match="p[@internalid]">
        <xsl:variable name="aknName">
            <xsl:if test="substring-after(./@class,' ') != ''">
                <xsl:value-of select="translate(substring-after(./@class,' '),'_','')" />
            </xsl:if>
            <xsl:if test="substring-after(./@class,' ') = ''">
                <xsl:value-of select="translate(@class,'_','')" />
            </xsl:if>
            <xsl:if test="./@class = ''">
            	<xsl:value-of select="name(.)" />
            </xsl:if>
        </xsl:variable>
	    <xsl:element name="{$aknName}">
        	<xsl:apply-templates select="@*" mode="aknPrefixAttributesWithoutId" />
       		<xsl:apply-templates />
		</xsl:element>
    </xsl:template>
	
	
	<!-- Content element -->
	<xsl:template match="div[contains(@class,'content')]">
		<xsl:variable name="aknName">
            <xsl:if test="substring-after(./@class,' ') != ''">
                <xsl:value-of select="translate(substring-after(./@class,' '),'_','')" />
            </xsl:if>
            <xsl:if test="substring-after(./@class,' ') = ''">
                <xsl:value-of select="translate(@class,'_','')" />
            </xsl:if>
            <xsl:if test="./@class = ''">
            	<xsl:value-of select="name(.)" />
            </xsl:if>
        </xsl:variable>
		<xsl:element name="{$aknName}">
            <xsl:apply-templates select="@*" mode="aknPrefixAttributes" />
        	<!-- Content element can not contains directly text so add a p element if it's needed -->
            <!--  and (count(child::text()) > 0) -->
            <xsl:call-template name="manageImplicitP"/>
        </xsl:element>
    </xsl:template>

    <xsl:template name="manageImplicitP">
        <xsl:choose>
            <xsl:when test="(count(div[contains(@class, 'block')]) = 0) and ./table">
                <p>
                    <xsl:apply-templates select="./table/preceding-sibling::node()"/>
                </p>
                <xsl:apply-templates select="./table"/>
                <p>
                    <xsl:apply-templates select="./table/following-sibling::node()"/>
                </p>
            </xsl:when>
            <xsl:when test="count(div[contains(@class, 'block') or contains(@class, 'container')]) = 0">
                <p>
                    <xsl:apply-templates />
                </p>
            </xsl:when>
            <!-- If there is exactly one block, which contains a table, split it. -->
            <xsl:when test="(count(div[contains(@class, 'block')]) = 1) and */table">
                <p>
                    <xsl:apply-templates select="*/table/preceding-sibling::node()"/>
                </p>
                <xsl:apply-templates select="*/table"/>
                <p>
                    <xsl:apply-templates select="*/table/following-sibling::node()"/>
                </p>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates />
            </xsl:otherwise>
        </xsl:choose> 
    </xsl:template>
	
	<xsl:template match="span[contains(@class,'documentRef')]">
		<xsl:variable name="aknName">
            <xsl:if test="substring-after(./@class,' ') != ''">
                <xsl:value-of select="translate(substring-after(./@class,' '),'_','')" />
            </xsl:if>
            <xsl:if test="substring-after(./@class,' ') = ''">
                <xsl:value-of select="translate(@class,'_','')" />
            </xsl:if>
            <xsl:if test="./@class = ''">
            	<xsl:value-of select="name(.)" />
            </xsl:if>
        </xsl:variable>
		<xsl:element name="{$aknName}">
			<xsl:apply-templates select="@*" mode="aknPrefixAttributes" />
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="*[contains(@class,'collectionBody')]">
		<xsl:variable name="aknName">
            <xsl:if test="substring-after(./@class,' ') != ''">
                <xsl:value-of select="translate(substring-after(./@class,' '),'_','')" />
            </xsl:if>
            <xsl:if test="substring-after(./@class,' ') = ''">
                <xsl:value-of select="translate(@class,'_','')" />
            </xsl:if>
            <xsl:if test="./@class = ''">
            	<xsl:value-of select="name(.)" />
            </xsl:if>
        </xsl:variable>
		<xsl:element name="{$aknName}">
			<xsl:apply-templates select="@*" mode="aknPrefixAttributesWithoutId" />
			<xsl:apply-templates />
		</xsl:element>
	</xsl:template>
	
	<!-- Authorial note -->
	<xsl:template match="div[contains(@class,'authorialNote')]">
	</xsl:template>
	
	<xsl:template match="div[contains(@class,'authorialNote')]" mode="replaceNote">
		<xsl:variable name="aknName">
			<xsl:if test="substring-after(./@class,' ') != ''">
				<xsl:value-of select="translate(substring-after(./@class,' '),'_','')" />
			</xsl:if>
			<xsl:if test="substring-after(./@class,' ') = ''">
				<xsl:value-of select="translate(@class,'_','')" />
			</xsl:if>
			<xsl:if test="./@class = ''">
				<xsl:value-of select="name(.)" />
			</xsl:if>
		</xsl:variable>
		<xsl:element name="{$aknName}">
			<xsl:apply-templates select="@*" mode="aknPrefixAttributes" />
			<xsl:choose>
				<xsl:when test="./p">
					<xsl:apply-templates />
				</xsl:when>
				<xsl:otherwise>
	    			<p>
						<xsl:apply-templates />
					</p>
	    		</xsl:otherwise>
			</xsl:choose>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="html:span[@class='posTmpSpan']">
		<xsl:variable name="noteId" select="@noteref" />
		<xsl:apply-templates  mode="replaceNote" select="//div[contains(@class,'authorialNote')][@notetmpid=$noteId]"/> 
	</xsl:template>
	
	<xsl:template match="span[@class='posTmpSpan']">
		<xsl:variable name="noteId" select="@noteref" />
		<xsl:apply-templates  mode="replaceNote" select="//div[contains(@class,'authorialNote')][@notetmpid=$noteId]"/> 
	</xsl:template>
    
    <!-- Wrap quotedText/quotedStructures with mod if it is missing -->
    <xsl:template match="span[contains(@class,'quotedText')][not(contains(../@class, 'mod'))]">
        <mod>
            <quotedText>
                <xsl:apply-templates select="@*" mode="aknPrefixAttributes" />
                <xsl:apply-templates />
            </quotedText>
        </mod>
    </xsl:template>
    
    <xsl:template match="div[contains(@class,'quotedStructure')][not(contains(../@class, 'mod'))]">
        <mod>
            <quotedStructure>
                <xsl:apply-templates select="@*" mode="aknPrefixAttributes" />
                <xsl:apply-templates />
            </quotedStructure>
        </mod>
    </xsl:template>

	
	<xsl:template match="*">
        <xsl:element name="{name(.)}">
        	<xsl:for-each select="@*">
        		<xsl:if test="name(.) = 'class' or name(.) = 'id'">
        			<xsl:attribute name="{name(.)}"><xsl:value-of select="." /></xsl:attribute>
        		</xsl:if>
		    </xsl:for-each>
		    <xsl:apply-templates select="@*" mode="aknPrefixAttributes" />
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>
    
    <!-- HTML elements -->
    <xsl:template match="br">
        <xsl:if test="contains(../@class, 'block') or contains(../@class, 'inline')">
            <eol />
        </xsl:if>
    </xsl:template>

	<xsl:template match="img">
		<xsl:element name="{name(.)}">
			<xsl:apply-templates select="@*" mode="allAttributes" />
			<xsl:apply-templates />
		</xsl:element>
	</xsl:template>

    <xsl:template match="strong">
		<xsl:element name="b">
        	<xsl:apply-templates select="@*" mode="aknPrefixAttributes" />
    		<xsl:apply-templates />
    	</xsl:element>
    </xsl:template>

    <xsl:template match="tbody">
        <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="td">
		<xsl:element name="td">
            <xsl:apply-templates select="@*" mode="aknPrefixAttributes" />
            <xsl:if test="@rowspan">
                <xsl:attribute name="rowspan"><xsl:value-of select="@rowspan" /></xsl:attribute>
            </xsl:if>
            <xsl:if test="@colspan">
                <xsl:attribute name="colspan"><xsl:value-of select="@colspan" /></xsl:attribute>
            </xsl:if>
            <xsl:if test="@style">
                <xsl:attribute name="style"><xsl:value-of select="@style" /></xsl:attribute>
            </xsl:if>
            <!-- Add p wrapper if we contain only text nodes -->
            <xsl:choose>
                <xsl:when test="count(div[contains(@class, 'block')])=0">
                    <xsl:element name="p">
                        <xsl:apply-templates />
                    </xsl:element>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates />
                </xsl:otherwise>
            </xsl:choose>
    	</xsl:element>
    </xsl:template>

    <xsl:template match="th">
		<xsl:element name="th">
		    <xsl:apply-templates select="@*" mode="aknPrefixAttributes" />
			<xsl:if test="@rowspan">
        		<xsl:attribute name="rowspan"><xsl:value-of select="@rowspan" /></xsl:attribute>
        	</xsl:if>
			<xsl:if test="@colspan">
        		<xsl:attribute name="colspan"><xsl:value-of select="@colspan" /></xsl:attribute>
        	</xsl:if>
			<xsl:if test="@style">
        		<xsl:attribute name="style"><xsl:value-of select="@style" /></xsl:attribute>
        	</xsl:if>
		    <xsl:apply-templates />
    	</xsl:element>
    </xsl:template>
    
	<!-- Elements to ignore -->
    <xsl:template match="   div[contains(@class,'akoma_ntoso')] | 
                            div[contains(@class, 'toMarkNode')] |
                            div[contains(@class, 'block p') and contains(../@class, 'hcontainer') and not(contains(../@class, 'item'))] |
                            div[contains(@class,'notesContainer')] |
                            span[not(@*)]">
        <xsl:apply-templates />
    </xsl:template>

    <xsl:template match="p[contains(@class, 'breaking')] |
                         span[contains(@class, 'breaking')]">
    </xsl:template>
    
    <!-- Called template -->
    <xsl:template match="div[contains(@class,'meta')]//div">  	
    	<xsl:variable name="aknName">
            <xsl:choose>
                <xsl:when test="substring-after(./@class,' ') != ''">
                    <xsl:value-of select="translate(substring-after(./@class,' '),'_','')" />
                </xsl:when>
                <xsl:otherwise>
                   <xsl:value-of select="@class" />
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
	    <xsl:element name="{$aknName}">
	    	<xsl:apply-templates select="@*" mode="aknPrefixAttributes" />
	    	<xsl:apply-templates select="@*[not(name() =  'class')]" mode="notAknPrefixAttributes" />
			<xsl:apply-templates />
		</xsl:element>
    </xsl:template>

    <xsl:template match="div[contains(@class,'meta')]//div[contains(@class,'FRBRWork') or 
                             contains(@class,'FRBRExpression') or 
                             contains(@class,'FRBRManifestation')]">
        <xsl:variable name="aknName">
            <xsl:choose>
                <xsl:when test="substring-after(./@class,' ') != ''">
                    <xsl:value-of select="translate(substring-after(./@class,' '),'_','')" />
                </xsl:when>
                <xsl:otherwise>
                   <xsl:value-of select="@class" />
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:element name="{$aknName}">
            <xsl:apply-templates select="@*" mode="aknPrefixAttributes" />
            <xsl:apply-templates select="@*[not(name() =  'class')]" mode="notAknPrefixAttributes" />
            <xsl:apply-templates select="./*[@class = 'FRBRthis']"/>
            <xsl:apply-templates select="./*[@class = 'FRBRuri']"/>
            <xsl:apply-templates select="./*[@class = 'FRBRalias']"/>
            <xsl:apply-templates select="./*[@class = 'FRBRdate']"/>
            <xsl:apply-templates select="./*[@class = 'FRBRauthor']"/>
            <xsl:apply-templates select="./*[@class = 'FRBRcountry']"/>

            <xsl:apply-templates select="./*[not(@class = 'FRBRthis') and 
                                            not(@class = 'FRBRuri') and 
                                            not(@class = 'FRBRalias') and 
                                            not(@class = 'FRBRdate') and 
                                            not(@class = 'FRBRauthor')and 
                                            not(@class = 'FRBRcountry')]"/>
        </xsl:element>
    </xsl:template>
    
    <!-- <xsl:template match="text()">
        <xsl:value-of select="normalize-space(.)"/>
   </xsl:template> -->
</xsl:stylesheet>
