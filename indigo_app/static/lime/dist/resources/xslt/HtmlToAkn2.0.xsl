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
	
    
	<xsl:template match="   div| 
    						span[@internalid] | 
                            p">
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
		        	<xsl:for-each select="@*">
		        		<xsl:if test="substring-before(name(.),'_') = 'akn'">
		        			<xsl:attribute name="{substring-after(name(.),'_')}"><xsl:value-of select="." /></xsl:attribute>
		        		</xsl:if>	
		        	</xsl:for-each>
		       		<xsl:apply-templates />
       			</xsl:element>
        	</xsl:when> 
        	<!-- All elements -->
		    <xsl:when test="$aknName != ''">
        	    <xsl:element name="{$aknName}">
		        	<xsl:for-each select="@*">
		        		<xsl:if test="substring-before(name(.),'_') = 'akn'">
		        			<xsl:attribute name="{substring-after(name(.),'_')}"><xsl:value-of select="." /></xsl:attribute>
		        		</xsl:if>	
		        	</xsl:for-each>
		       		<xsl:apply-templates />
       			</xsl:element>
        	</xsl:when>
        	<xsl:otherwise>
        	   <xsl:apply-templates />
        	</xsl:otherwise>
        </xsl:choose>
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
			<xsl:for-each select="@*">
				<xsl:if test="substring-before(name(.),'_') = 'akn'">
					<xsl:attribute name="{substring-after(name(.),'_')}"><xsl:value-of select="." /></xsl:attribute>
				</xsl:if>	
				</xsl:for-each>
			<xsl:apply-templates />
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="html:span[@class='posTmpSpan']">
		<xsl:variable name="noteId" select="@chposid" />
		<xsl:apply-templates  mode="replaceNote" select="//div[contains(@class,'authorialNote')][@chpos_id=$noteId]"/> 
	</xsl:template>
    
	
	<xsl:template match="*">
        <xsl:element name="{name(.)}">
        	<xsl:for-each select="@*">
		    	<xsl:if test="substring-before(name(.),'_') = 'akn'">
		        	<xsl:attribute name="{substring-after(name(.),'_')}"><xsl:value-of select="." /></xsl:attribute>
		        </xsl:if>
		        <xsl:if test="name(.) = 'class' or name(.) = 'id'">
        			<xsl:attribute name="{name(.)}"><xsl:value-of select="." /></xsl:attribute>
        		</xsl:if>
		    </xsl:for-each>
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>
    
    <!-- HTML elements -->
    <xsl:template match="br">
    	<eol />
    </xsl:template>
	<xsl:template match="img">
		<xsl:element name="{name(.)}">
			<xsl:for-each select="@*">
				<xsl:attribute name="{name(.)}">
					<xsl:value-of select="." />
				</xsl:attribute>
			</xsl:for-each>
			<xsl:apply-templates />
		</xsl:element>
	</xsl:template>

    <xsl:template match="strong">
		<xsl:element name="b">
        	<xsl:for-each select="@*">
		    	<xsl:if test="substring-before(name(.),'_') = 'akn'">
		        	<xsl:attribute name="{substring-after(name(.),'_')}"><xsl:value-of select="." /></xsl:attribute>
		        </xsl:if>	
		    </xsl:for-each>
    		<xsl:apply-templates />
    	</xsl:element>
    </xsl:template>

    <xsl:template match="p">
		<xsl:element name="{name(.)}">
        	<xsl:for-each select="@*">
		    	<xsl:if test="substring-before(name(.),'_') = 'akn'">
		        	<xsl:attribute name="{substring-after(name(.),'_')}"><xsl:value-of select="." /></xsl:attribute>
		        </xsl:if>	
		    </xsl:for-each>
    		<xsl:apply-templates />
    	</xsl:element>
    </xsl:template>

    <xsl:template match="td">
		<xsl:element name="td">
		    <xsl:for-each select="@*">
		    	<xsl:if test="substring-before(name(.),'_') = 'akn'">
		        	<xsl:attribute name="{substring-after(name(.),'_')}"><xsl:value-of select="." /></xsl:attribute>
		        </xsl:if>	
		    </xsl:for-each>
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

    <xsl:template match="th">
		<xsl:element name="th">
		    <xsl:for-each select="@*">
		    	<xsl:if test="substring-before(name(.),'_') = 'akn'">
		        	<xsl:attribute name="{substring-after(name(.),'_')}"><xsl:value-of select="." /></xsl:attribute>
		        </xsl:if>	
		    </xsl:for-each>
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
                            p[contains(../@class, 'hcontainer')]">
        <xsl:apply-templates />
    </xsl:template>
    
    <!-- Called template -->
    <xsl:template match="div[contains(@class,'meta')]//div">
    	
    	<xsl:variable name="aknName">
                <xsl:value-of select="@class" />
        </xsl:variable>
        	    <xsl:element name="{$aknName}">
		        	<xsl:for-each select="@*[not(name() =  'class')]">
		        		<xsl:attribute name="{name(.)}"><xsl:value-of select="." /></xsl:attribute>
		        	</xsl:for-each>
                               <xsl:apply-templates />
       			</xsl:element>
       			<!-- <meta>
			<identification source="">
				<FRBRWork>
					<FRBRthis value=""/>
					<FRBRuri value=""/>
					<FRBRdate date="" name=""/>
					<FRBRauthor href="" as=""/>
					<componentInfo>
						<componentData id="" href="" name="" showAs=""/>
					</componentInfo>
					<FRBRcountry value=""/>
				</FRBRWork>
				<FRBRExpression>
					<FRBRthis value=""/>
					<FRBRuri value=""/>
					<FRBRdate date="" name=""/>
					<FRBRauthor href="" as=""/>
					<componentInfo>
						<componentData id="" href="" name="" showAs=""/>
					</componentInfo>
					<FRBRlanguage language=""/>
				</FRBRExpression>
				<FRBRManifestation>
					<FRBRthis value=""/>
					<FRBRuri value=""/>
					<FRBRdate date="" name=""/>
					<FRBRauthor href="" as=""/>
					<componentInfo>
						<componentData id="" href="" name="" showAs=""/>
					</componentInfo>
				</FRBRManifestation>
			</identification>
			<references source="">
				<original id="" href="" showAs=""/>
				<hasAttachment id="" href="" showAs=""/>
				<TLCOrganization id="" href="" showAs=""/>
				<TLCPerson id="" href="" showAs=""/>
				<TLCRole id="" href="" showAs=""/>
			</references>
		</meta> -->
</xsl:template>
    
    <xsl:template match="text()">
        <xsl:value-of select="normalize-space(.)"/>
    </xsl:template>
</xsl:stylesheet>