<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xml="http://www.w3.org/XML/1998/namespace"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:akn="http://www.akomantoso.org/2.0"
    exclude-result-prefixes="xs"
    version="1.0">
    <xsl:output method="xml" indent="yes" encoding="UTF-8" />
    
    <xsl:template match="/">
    	<div>
        	<xsl:apply-templates />
        </div>
    </xsl:template>
    
    <xsl:template match="akomaNtoso">
        	<xsl:apply-templates />
    </xsl:template>

	<!-- ATTRIBUTE'S GENERIC TEMPLATE -->
	<xsl:template mode="elementAttributes" match="@*" >
    	<xsl:choose> 
    		<xsl:when test="not(starts-with(name(.),'xml'))">
    			<xsl:variable name="attName" select="concat('akn_',name(.))"/>
    			<xsl:attribute name="{$attName}">
    				<xsl:value-of select="." />
    			</xsl:attribute>	
    		</xsl:when>
    		<xsl:otherwise>
    			<xsl:attribute name="{name(.)}">
    				<xsl:value-of select="." />
    			</xsl:attribute>	
    		</xsl:otherwise>
    	</xsl:choose>	
    </xsl:template>
	
	<!-- UNDEFINED ATTRIBUTE'S GENERIC TEMPLATE -->
	<xsl:template mode="undefinedElementAttributes" match="@*" >
			<xsl:attribute name="{name(.)}">
				<xsl:value-of select="." />
			</xsl:attribute>	
	</xsl:template>
	
	<!--<xsl:template match="*[not(name(.)='akomaNtoso')]">
	        <div>
	        	<xsl:attribute name="class">
		         	<xsl:value-of select="name(.)" />
		         </xsl:attribute>
		         <xsl:attribute name="internalid">
		         	<xsl:value-of select="name(.)" />
		         </xsl:attribute>
	        	
	        	 ATTRIBUTE'S GENERIC TEMPLATE  
	        	<xsl:apply-templates select="@*" mode="elementAttributes" />
	            <xsl:apply-templates />
	        </div>
	</xsl:template> --> 

	<!-- Document type -->
	<xsl:template match="akn:bill |
		akn:act |
		akn:doc |
		akn:judgement |
		akn:documentCollection |
		akn:amendmentList |
		akn:amendment |
		akn:debateReport |
		akn:officialGazette |
		akn:statement |
		akn:debate">
		<div>
			<xsl:attribute name="class">
				<xsl:value-of select="concat('document ',name(.))" />
			</xsl:attribute>
			
			<!-- ATTRIBUTE'S GENERIC TEMPLATE -->
			<xsl:apply-templates select="@*" mode="elementAttributes" />
			<xsl:apply-templates/>
		</div>   	
	</xsl:template>    
	
	<!-- Container elements xml-->
	<xsl:template match="akn:blockList |
					     akn:blockContainer |
					     akn:intro |
					     akn:wrap |
					     akn:tblock |
					     akn:toc |
					     akn:foreign |
					     akn:coverPage |
					     akn:container |
					     akn:preface |
					     akn:preamble |
					     akn:recital |
					     akn:citation |
					     akn:conclusions |
					     akn:body |
					     akn:mainBody |
					     akn:administrationOfOath |
					     akn:speechGroup |
					     akn:speech |
					     akn:question |
					     akn:answer |
					     akn:amendmentHeading |
						 akn:amendmentContent |
						 akn:amendmentReference |
						 akn:header |
						 akn:amendmentJustification |
						 akn:introduction |
						 akn:background |
						 akn:arguments |
						 akn:remedias |
						 akn:motivation |
						 akn:decision |
						 akn:fragmentBody
						">
	        <div>
	        	<xsl:attribute name="class">
		         	<xsl:value-of select="concat('container ',name(.))" />
		         </xsl:attribute>
		         <xsl:attribute name="internalid">
		         	<xsl:value-of select="name(.)" />
		         </xsl:attribute>
	        	
	        	<!-- ATTRIBUTE'S GENERIC TEMPLATE -->
	        	<xsl:apply-templates select="@*" mode="elementAttributes" />
	        	<xsl:apply-templates />
	        </div>
	</xsl:template>
	
	<!-- Block elements -->
	<xsl:template match="akn:block |
						akn:longTitle |
						akn:formula |
						akn:interstitial |
						akn:other
						">
	        <div>
	        	<xsl:attribute name="class">
		         	<xsl:value-of select="concat('block ',name(.))" />
		         </xsl:attribute>
		         <xsl:attribute name="internalid">
		         	<xsl:value-of select="name(.)" />
		         </xsl:attribute>
	        	
	        	<!-- ATTRIBUTE'S GENERIC TEMPLATE -->
	        	<xsl:apply-templates select="@*" mode="elementAttributes" />
	        	<xsl:apply-templates />
	        </div>
	</xsl:template>
	
	<!-- Marker elements -->
	<xsl:template match="akn:noteRef |
						 akn:eop |
						 akn:marker
						">
	        <span>
	        	<xsl:attribute name="class">
		         	<xsl:value-of select="concat('marker ',name(.))" />
		         </xsl:attribute>
		         <xsl:attribute name="internalid">
		         	<xsl:value-of select="name(.)" />
		         </xsl:attribute>
	        	
	        	<!-- ATTRIBUTE'S GENERIC TEMPLATE -->
	        	<xsl:apply-templates select="@*" mode="elementAttributes" />
	        	<xsl:apply-templates />
	        </span>
	</xsl:template>
	
	<xsl:template match="akn:eol">
	        <br>	        	
	        	<!-- ATTRIBUTE'S GENERIC TEMPLATE -->
	        	<xsl:apply-templates select="@*" mode="elementAttributes" />
	        	<xsl:apply-templates />
	        </br>
	</xsl:template>
	
	<!-- Popup elements -->
	<xsl:template match="akn:authorialNote">
			<div>
	        	<xsl:attribute name="class">
		         	<xsl:value-of select="concat('popup ',name(.))" />
		         </xsl:attribute>
		         <xsl:attribute name="internalid">
		         	<xsl:value-of select="name(.)" />
		         </xsl:attribute>
	        	
	        	<!-- ATTRIBUTE'S GENERIC TEMPLATE -->
	        	<xsl:apply-templates select="@*" mode="elementAttributes" />
	        	<xsl:apply-templates />
	        </div>
	</xsl:template>
	
	
	<!-- Hcontainer elements -->
	<xsl:template match="akn:clause |
						akn:recitals |
						akn:citations |
						akn:item |
						akn:hcontainer |
						akn:rollCall |
						akn:pryers |
						akn:oralStatements |
						akn:writtenStatements |
						akn:personalStatements |
						akn:ministerialStatements |
						akn:resolutions |
						akn:nationalInterest |
						akn:declarationOfVote |
						akn:comunication |
						akn:petitions |
						akn:papers |
						akn:noticesOfMotion |
						akn:questions |
						akn:address |
						akn:proceduralMotions |
						akn:pointOfOrder |
						akn:adjournement |
						akn:debateSection |
						akn:section |
						akn:part |
						akn:paragraph |
						akn:chapter |
						akn:title |
						akn:article |
						akn:book |
						akn:tome |
						akn:division |
						akn:list |
						akn:point |
						akn:indent |
						akn:alinea |
						akn:rule |
						akn:subrule |
						akn:proviso |
						akn:subsection |
						akn:subpart |
						akn:subparagraph |
						akn:subchapter |
						akn:subtitle |
						akn:subdivision |
						akn:subclause |
						akn:sublist |
						akn:transitional
						">
	        <div>
	        	<xsl:attribute name="class">
		         	<xsl:value-of select="concat('hcontainer ',name(.))" />
		         </xsl:attribute>
		         <xsl:attribute name="internalid">
		         	<xsl:value-of select="name(.)" />
		         </xsl:attribute>
	        	
	        	<!-- ATTRIBUTE'S GENERIC TEMPLATE -->
	        	<xsl:apply-templates select="@*" mode="elementAttributes" />
	        	<xsl:apply-templates />
	        </div>
	</xsl:template>
	
	<!-- Undefined elements -->
	<xsl:template match="akn:quotedStructure|
						akn:amendmentList |
						akn:meta |
						akn:identification |
						akn:FRBRWork |
						akn:FRBRthis |
						akn:FRBRuri |
						akn:FRBRalias |
						akn:FRBRdate |
						akn:FRBRauthor |
						akn:componentInfo |
						akn:componentData |
						akn:preservation |
						akn:FRBRcountry |
						akn:FRBRsubtype |
						akn:FRBRnumber |
						akn:FRBRname |
						akn:FRBRprescriptive |
						akn:FRBRauthoritative |
						akn:FRBRExpression |
						akn:FRBRlanguage |
						akn:FRBRtranslation |
						akn:FRBRManifestation |
						akn:FRBRformat |
						akn:FRBRItem |
						akn:publication |
						akn:classification |
						akn:keyword |
						akn:lifecycle |
						akn:eventRef |
						akn:workflow |
						akn:step |
						akn:analysis |
						akn:activeModifications |
						akn:textualMod |
						akn:source |
						akn:destination |
						akn:force |
						akn:efficacy |
						akn:application |
						akn:duration |
						akn:condition |
						akn:old |
						akn:new |
						akn:meaningMod |
						akn:domain |
						akn:scopeMod |
						akn:forceMod |
						akn:efficacyMod |
						akn:legalSystemMod |
						akn:passiveModifications |
						akn:judicial |
						akn:result |
						akn:supports |
						akn:isAnalogTo |
						akn:applies |
						akn:extends |
						akn:restricts |
						akn:derogates |
						akn:contrasts |
						akn:overrules |
						akn:dissentsFrom |
						akn:putsInQuestion |
						akn:distingushes |
						akn:parliamentary |
						akn:quprumVerification |
						akn:quorum |
						akn:count |
						akn:voting |
						akn:recount |
						akn:otherAnalysis |
						akn:temporalData |
						akn:temporalGroup |
						akn:timeInterval |
						akn:renamberingInfo |
						akn:references |
						akn:original |
						akn:passiveRef |
						akn:activeRef |
						akn:jurisprudence |
						akn:hasAttachment |
						akn:attachmentOf |
						akn:TLCPerson |
						akn:TLCOrganization |
						akn:TLCConcept |
						akn:TCLObject |
						akn:TLCEvent |
						akn:TLCLocation |
						akn:TLCProcess |
						akn:TLCRole |
						akn:TLCTerm |
						akn:TLCReference |
						akn:notes |
						akn:note |
						akn:componentRef |
						akn:proprietary |
						akn:presentation |
						akn:collectionBody |
						akn:documentRef |
						akn:attachments |
						akn:components |
						akn:component |
						akn:debateBody |
						akn:amendmentBody |
						akn:judgementBody |
						akn:fragment |
						akn:extractStructure |
						akn:subFlow
						">
	        <div>
	        	<xsl:attribute name="class">
		         	<xsl:value-of select="name(.)" />
		         </xsl:attribute>
		         <!-- <xsl:attribute name="internalid">
		         	<xsl:value-of select="name(.)" />
		       </xsl:attribute> -->
	        	
	        	<!-- UNDEFINED ATTRIBUTE'S GENERIC TEMPLATE -->
	        	<xsl:apply-templates select="@*" mode="undefinedElementAttributes" />
	        	<xsl:apply-templates />
	        </div>
	</xsl:template>
	
	<!-- Inline elements -->
	<xsl:template match="akn:listIntroduction |
						 akn:listConclusion |
						 akn:docDate |
						 akn:docNumber |
						 akn:docTitle |
						 akn:location |
						 akn:docType |
						 akn:heading |
						 akn:num |
						 akn:proponent |
						 akn:signature |
						 akn:role |
						 akn:person |
						 akn:quotedText |
						 akn:subheading |
						 akn:ref |
						 akn:mref |
						 akn:rref |
						 akn:date |
						 akn:time |
						 akn:organization |
						 akn:concept |
						 akn:object |
						 akn:event |
						 akn:process |
						 akn:from |
						 akn:term |
						 akn:quantity |
						 akn:def |
						 akn:entity |
						 akn:courtType |
						 akn:neutralCitation |
						 akn:party |
						 akn:judge |
						 akn:lower |
						 akn:scene |
						 akn:opinion |
						 akn:argument |
						 akn:affectedDocument |
						 akn:relatedDocument |
						 akn:change |
						 akn:inline |
						 akn:mmod |
						 akn:rmod |
						 akn:remark |
						 akn:recorderedTime |
						 akn:vote |
						 akn:outcome |
						 akn:ins |
						 akn:del |
						 akn:mod |
						 akn:legislature |
						 akn:session |
						 akn:shortTitle |
						 akn:docPurpose |
						 akn:docCommittee |
						 akn:docIntroducer |
						 akn:docStage |
						 akn:docStatus |
						 akn:docJurisdiction |
						 akn:docketNumber |
						 akn:placeholder |
						 akn:fillIn |
						 akn:decoration |
						 akn:docProponent |
						 akn:omissis |
						 akn:extractText |
						 akn:narrative |
						 akn:summery |
						 akn:tocItem">
	        <span>
	        	<xsl:attribute name="class">
		         	<xsl:value-of select="concat('inline ',name(.))" />
		         </xsl:attribute>
		         <xsl:attribute name="internalid">
		         	<xsl:value-of select="name(.)" />
		         </xsl:attribute>
	        	
	        	<!-- ATTRIBUTE'S GENERIC TEMPLATE -->
	        	<xsl:apply-templates select="@*" mode="elementAttributes" />
	        	<xsl:apply-templates />
	        </span>
	</xsl:template>
	
	<!-- Html elements -->
	<xsl:template match="akn:p |
						akn:span |
						akn:a |
						akn:b |
						akn:i|
						akn:u |
						akn:sub |
						akn:sup |
						akn:abbr |
						akn:br |
						akn:div |
						akn:img |
						akn:li |
						akn:ol |
						akn:ul |
						akn:table |
						akn:td |
						akn:th |
						akn:caption |
						akn:tr">
	        <xsl:element name="{name(.)}">
	        	<!-- TODO: check the specific HTML elements attributes -->
	        	
	        	<!-- ATTRIBUTE'S GENERIC TEMPLATE -->
	        	<xsl:apply-templates select="@*" mode="undefinedElementAttributes" />
	    
	        	<xsl:apply-templates />
    	</xsl:element>
	</xsl:template>
	
    
    <xsl:template match="text()">
        <xsl:value-of select="normalize-space(.)"/>
    </xsl:template>
    
    <!-- Elements to remove -->
    <xsl:template match="content">
    		<xsl:apply-templates />
    </xsl:template>
    
    <xsl:template match="meta">
    	<div class="meta">
    		<xsl:apply-templates />
    	</div>
    </xsl:template>
</xsl:stylesheet>