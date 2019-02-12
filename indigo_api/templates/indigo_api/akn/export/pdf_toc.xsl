<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:outline="http://wkhtmltopdf.org/outline"
                xmlns="http://www.w3.org/1999/xhtml">
  <xsl:output doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN"
              doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"
              indent="yes" />
  <xsl:template match="outline:outline">
    <html>
      <head>
        <title>Table of Contents</title>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <style>
          body {
            font-family: Georgia, "Times New Roman", serif;
            font-size: 12pt;
            line-height: 1.4;
          }
          h1 {
            text-align: center;
            font-size: 18pt;
            margin-top: 0px;
            margin-bottom: 2em;
          }
          ol {
            font-size: 14pt;
            padding-left: 0px;
            margin-bottom: 1em;
          }
          ol ol {
            font-size: 12pt;
            padding-left: 1em;
          }
          li {list-style: none; clear: both;}
          .page {
            float: right;
            font-size: 12pt;
          }
          a {text-decoration:none; color: black;}
        </style>
      </head>
      <body>
        <h1>Table of Contents</h1>
        <ol><xsl:apply-templates select="outline:item/outline:item"/></ol>
      </body>
    </html>
  </xsl:template>
  <xsl:template match="outline:item">
    <li>
      <xsl:if test="@title != '' and @title != 'Table of Contents'">
        <div class="entry">
          <a>
            <xsl:if test="@link">
              <xsl:attribute name="href"><xsl:value-of select="@link"/></xsl:attribute>
            </xsl:if>
            <xsl:if test="@backLink">
              <xsl:attribute name="name"><xsl:value-of select="@backLink"/></xsl:attribute>
            </xsl:if>
            <xsl:value-of select="@title" />
          </a>
          <span class="page"> <xsl:value-of select="@page" /> </span>
        </div>
      </xsl:if>
      <xsl:if test="*">
        <ol>
          <xsl:comment>added to prevent self-closing tags in QtXmlPatterns</xsl:comment>
          <xsl:apply-templates select="outline:item"/>
        </ol>
      </xsl:if>
    </li>
  </xsl:template>
</xsl:stylesheet>
