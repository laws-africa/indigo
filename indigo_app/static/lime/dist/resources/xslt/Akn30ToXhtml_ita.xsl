<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
   xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD03" exclude-result-prefixes="akn"
   version="2.0">
   <xsl:output method="xml" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"
      doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN" indent="yes"/>
   <xsl:template match="/">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="text()">
      <xsl:value-of select="normalize-space(.)"/>
   </xsl:template>
   <xsl:template match="akn:akomaNtoso">
      <html xmlns="http://www.w3.org/1999/xhtml">
         <head>
            <title>AkomaNtoso document</title>
            <style type="text/css">
               html{
               }
               body{
                   padding:10px;
               }
               .coverPage{
                   text-align:center;
               }
               
               .preface{
                   text-align:center;
                   width:80%;
                   margin-left:auto;
                   margin-right:auto;
               }
               
               .preface .docTitle{
                   font-weight:bold;
                   display:block;
               }
               .preface .docNumber{
                   font-weight:bold;
                   display:block;
               }
               .preface .docType{
                   font-weight:bold;
                   display:block;
               }
               .preface .docDate{
                   font-style:italic;
                   display:block;
               }
               .preface .docProponent{
                   font-style:italic;
               }
               .preamble p{
                   text-indent:10px;
               }
               
               .listIntroduction{
                   display:block;
                   font-style:italic;
                   margin-bottom:10px;
               }
               
               ul{
                   list-style:none;
                   margin:0px;
                   padding:0px;
               }
               
               .blockList{
                   margin-left:10px;
               }
               
               li .num{
                   display:inline;
                   float:left;
                   margin-right:5px;
               }
               
               .point .num{
                   display:inline;
                   float:left;
                   margin-right:5px;
               }
               
               p[data-class = centrado]{
                   text-align:center;
               }
               p[data-class = center]{
                   text-align:center;
               }
               p[data-class = centrato]{
                   text-align:center;
               }
               
               .hierarchy{
                   margin-left:10px;
               }
               
               .body > .hierarchy > .content > p > .docTitle{
                   display:block;
                   text-align:center;
                   font-weight:bold;
               }
               
               .title > .num{
                   display:block;
                   margin-bottom:5px;
               }
               .chapter > .num{
                   display:block;
                   margin-bottom:5px;
               }
               .chapter > .heading{
                   display:block;
                   margin-bottom:5px;
               }
               .chapter > .subheading{
                   display:block;
                   margin-bottom:5px;
               }
               
               .article .num{
                   font-weight:bold;
                   display:block;
                   text-align:center;
               }
               .article .heading{
                   font-style:italic;
                   display:block;
                   text-align:center;
                   width:100%;
               }
               .section .num{
                   display:inline;
                   float:left;
                   margin-right:5px;
               }
               
               .section .heading{
               
               }
               
               .clause{
                   margin-left:0px;
               }
               .conclusions p{
                   font-weight:bold;
               }
               
               .paragraph .num{
                   display:block;
                   float:left;
                   margin-right:5px;
               }</style>
         </head>
         <body>
            <xsl:apply-templates/>
         </body>
      </html>
   </xsl:template>
   <xsl:template match="akn:doc">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:mainBody">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:statement">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:amendmentList">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:officialGazette">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:documentCollection">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:interstitial">
      <xsl:variable name="class" select="concat(local-name(.),' blocksreq')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:collectionBody">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:fragment">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:fragmentBody">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:act">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:bill">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:body">
      <xsl:variable name="class" select="concat(local-name(.),' bodyType')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:debateReport">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:debate">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:debateBody">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:judgement">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:judgementBody">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:amendment">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:amendmentBody">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:recitals">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:recital">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:citations">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:citation">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:longTitle">
      <xsl:variable name="class" select="concat(local-name(.),' blocksreq')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:formula">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:coverPage">
      <xsl:variable name="class" select="concat(local-name(.),' basicopt')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:preamble">
      <xsl:variable name="class" select="concat(local-name(.),' preambleopt')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:preface">
      <xsl:variable name="class" select="concat(local-name(.),' prefaceopt')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:conclusions">
      <xsl:variable name="class" select="concat(local-name(.),' basicopt')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:header">
      <xsl:variable name="class" select="concat(local-name(.),' blocksopt')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:attachments">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:componentRef">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <a>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:attribute name="src" select="@src"/>
         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </a>
   </xsl:template>
   <xsl:template match="akn:documentRef">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchicalStructure')"/>
      <a>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:attribute name="src" select="@src"/>
         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </a>
   </xsl:template>
   <xsl:template match="akn:clause">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:section">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:part">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:paragraph">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:chapter">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:title">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:book">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:tome">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:article">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:division">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:list">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:point">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:indent">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:alinea">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:subsection">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:subpart">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:subparagraph">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:subchapter">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:subtitle">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:subdivision">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:subclause">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:sublist">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:transitional">
      <xsl:variable name="class" select="concat(local-name(.),' hierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:content">
      <xsl:variable name="class" select="concat(local-name(.),' blocksreq')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:num">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:heading">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:subheading">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:intro">
      <xsl:variable name="class" select="concat(local-name(.),' blocksreq')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:wrap">
      <xsl:variable name="class" select="concat(local-name(.),' blocksreq')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:administrationOfOath">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:rollCall">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:prayers">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:oralStatements">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:writtenStatements">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:personalStatements">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:ministerialStatements">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:resolutions">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:nationalInterest">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:declarationOfVote">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:communication">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:petitions">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:papers">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:noticesOfMotion">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:questions">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:address">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:proceduralMotions">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:pointOfOrder">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:adjournment">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:debateSection">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:speechGroup">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:speech">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:question">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:answer">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:other">
      <xsl:variable name="class" select="concat(local-name(.),' blocksreq')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:scene">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:narrative">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:summary">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:from">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:vote">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:outcome">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:introduction">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:background">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:arguments">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:remedies">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:motivation">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:decision">
      <xsl:variable name="class" select="concat(local-name(.),' althierarchy')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:affectedDocument">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <a>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:attribute name="href" select="@href"/>
         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </a>
   </xsl:template>
   <xsl:template match="akn:relatedDocument">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <a>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:attribute name="href" select="@href"/>
         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </a>
   </xsl:template>
   <xsl:template match="akn:change">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:amendmentHeading">
      <xsl:variable name="class" select="concat(local-name(.),' blocksopt')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:amendmentContent">
      <xsl:variable name="class" select="concat(local-name(.),' blocksopt')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:amendmentReference">
      <xsl:variable name="class" select="concat(local-name(.),' blocksopt')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:amendmentJustification">
      <xsl:variable name="class" select="concat(local-name(.),' blocksopt')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:blockList">
      <xsl:variable name="class" select="concat(local-name(.),' blocksopt')"/>
      <ul>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </ul>
   </xsl:template>
   <xsl:template match="akn:item">
      <xsl:variable name="class" select="concat(local-name(.),' blocksopt')"/>
      <li>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </li>
   </xsl:template>
   <xsl:template match="akn:listIntroduction">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:listConclusion">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:tblock">
      <xsl:variable name="class" select="concat(local-name(.),' blocksopt')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:toc">
      <xsl:variable name="class" select="concat(local-name(.),' blocksopt')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:tocItem">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:docType">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:docTitle">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:docNumber">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:docProponent">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:docDate">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:legislature">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:session">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:shortTitle">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:docPurpose">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:docCommittee">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:docIntroducer">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:docStage">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:docStatus">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:docJurisdiction">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:docketNumber">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:courtType">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:neutralCitation">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:party">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:judge">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:lawyer">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:opinion">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:signature">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:date">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:time">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:entity">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:person">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:organization">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:concept">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:object">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:event">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:location">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:process">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:role">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:term">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:quantity">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:def">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:ref">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <a>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:attribute name="href" select="@href"/>
         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </a>
   </xsl:template>
   <xsl:template match="akn:mref">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:rref">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:mod">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:mmod">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:rmod">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:quotedText">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:remark">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:recordedTime">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:ins">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:del">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:omissis">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:placeholder">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:fillIn">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:noteRef">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <!--<a>
         <xsl:attribute name="class" select="$class"/>
<xsl:attribute name="id" select="@id"/>
<xsl:attribute name="style" select="@style"/>
        
         <xsl:attribute name="href" select="@ref"/>
         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each> -->
      <xsl:apply-templates/>
      <!--</a>-->
   </xsl:template>
   <xsl:template match="akn:eol">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <br>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
      </br>
   </xsl:template>
   <xsl:template match="akn:eop">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:quotedStructure">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:extractText">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:extractStructure">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:authorialNote">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:popup">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:foreign">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:hcontainer">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:container">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:block">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:inline">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:marker">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:attribute name="href" select="@ref"/>
         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:div">
      <xsl:variable name="class" select="concat(local-name(.),' blocksreq')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:p">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <p>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </p>
   </xsl:template>
   <xsl:template match="akn:span">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <span>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </span>
   </xsl:template>
   <xsl:template match="akn:br">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <br>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
      </br>
   </xsl:template>
   <xsl:template match="akn:b">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <strong>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </strong>
   </xsl:template>
   <xsl:template match="akn:i">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <emph>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </emph>
   </xsl:template>
   <xsl:template match="akn:u">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <u>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </u>
   </xsl:template>
   <xsl:template match="akn:sup">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <sup>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </sup>
   </xsl:template>
   <xsl:template match="akn:sub">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <sub>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </sub>
   </xsl:template>
   <xsl:template match="akn:abbr">
      <xsl:variable name="class" select="concat(local-name(.),' inline')"/>
      <abbr>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </abbr>
   </xsl:template>
   <xsl:template match="akn:a">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <a>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:attribute name="href" select="@href"/>
         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </a>
   </xsl:template>
   <xsl:template match="akn:img">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <img>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:attribute name="src" select="@src"/>
         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </img>
   </xsl:template>
   <xsl:template match="akn:ul">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <ul>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </ul>
   </xsl:template>
   <xsl:template match="akn:ol">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <ol>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </ol>
   </xsl:template>
   <xsl:template match="akn:li">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <li>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </li>
   </xsl:template>
   <xsl:template match="akn:table">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <table>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </table>
   </xsl:template>
   <xsl:template match="akn:caption">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <caption>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </caption>
   </xsl:template>
   <xsl:template match="akn:tr">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <tr>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </tr>
   </xsl:template>
   <xsl:template match="akn:th">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <th>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </th>
   </xsl:template>
   <xsl:template match="akn:td">
      <xsl:variable name="class" select="concat(local-name(.),' ')"/>
      <td>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </td>
   </xsl:template>
   <xsl:template match="akn:meta">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:identification">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRWork">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRExpression">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRManifestation">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRItem">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRthis">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRuri">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRalias">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRdate">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRauthor">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRlanguage">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRtranslation">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRsubtype">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRcountry">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRnumber">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRname">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRformat">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRprescriptive">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:FRBRauthoritative">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:componentInfo">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:componentData">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:preservation">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:publication">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:classification">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:keyword">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:lifecycle">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:eventRef">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:workflow">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:step">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:analysis">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:activeModifications">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:passiveModifications">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:textualMod">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:meaningMod">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:scopeMod">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:forceMod">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:efficacyMod">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:legalSystemMod">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:judicial">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:result">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:supports">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:isAnalogTo">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:applies">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:extends">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:restricts">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:derogates">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:contrasts">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:overrules">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:dissentsFrom">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:putsInQuestion">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:distinguishes">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:parliamentary">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:quorumVerification">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:voting">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:recount">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:quorum">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:count">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:otherAnalysis">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:source">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:destination">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:force">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:efficacy">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:application">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:duration">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:condition">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:old">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:new">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:domain">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:temporalData">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:temporalGroup">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:timeInterval">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:references">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:original">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:passiveRef">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:activeRef">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:jurisprudence">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:hasAttachment">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:attachmentOf">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:TLCPerson">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:TLCOrganization">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:TLCConcept">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:TLCObject">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:TLCEvent">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:TLCLocation">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:TLCProcess">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:TLCRole">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:TLCTerm">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:TLCReference">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:notes">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:note">
      <xsl:variable name="class" select="concat(local-name(.),' blocksreq')"/>
      <div>
         <xsl:attribute name="class" select="$class"/>
         <xsl:attribute name="id" select="@id"/>
         <xsl:attribute name="style" select="@style"/>

         <xsl:for-each select="@*">
            <xsl:variable name="attName" select="concat('data-',local-name(.))"/>
            <xsl:attribute name="{$attName}" select="."/>
         </xsl:for-each>
         <xsl:apply-templates/>
      </div>
   </xsl:template>
   <xsl:template match="akn:proprietary">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:presentation">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:components">
      <xsl:apply-templates/>
   </xsl:template>
   <xsl:template match="akn:component">
      <xsl:apply-templates/>
   </xsl:template>
</xsl:stylesheet>
