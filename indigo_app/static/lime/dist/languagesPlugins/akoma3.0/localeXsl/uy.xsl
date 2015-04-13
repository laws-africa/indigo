<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:uy="http://uruguay/propetary.xsd" version="1.0">

	<xsl:template match="uy:*">
	        <div class="{name()}">
	            <xsl:apply-templates/>
	        </div>
	</xsl:template>

	<xsl:template match="*[local-name(.) = 'div' and substring-before(./@class,':') = 'uy']">
        <xsl:element name="{@class}">
       		<xsl:apply-templates />
		</xsl:element>
	</xsl:template>
	
</xsl:stylesheet>