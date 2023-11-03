<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:fo="http://www.w3.org/1999/XSL/Format"
                xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <xsl:output method="xml"/>

  <xsl:include href="_blocks.xsl"/>
  <xsl:include href="_coverpage.xsl"/>
  <xsl:include href="_footnotes.xsl"/>
  <xsl:include href="_front-matter.xsl"/>
  <xsl:include href="_hier.xsl"/>
  <xsl:include href="_images.xsl"/>
  <xsl:include href="_inlines.xsl"/>
  <xsl:include href="_preface-preamble.xsl"/>
  <xsl:include href="_quotes.xsl"/>
  <xsl:include href="_tables.xsl"/>
  <xsl:include href="_toc.xsl"/>
  <xsl:include href="_variables.xsl"/>

  <xsl:strip-space elements="*"/>
  <!-- preserve whitespace for inline elements that can legitimately contain meaningful whitespace -->
  <xsl:preserve-space elements="akn:a akn:affectedDocument akn:b akn:block akn:caption akn:change akn:concept akn:courtType akn:date akn:def akn:del akn:docCommittee akn:docDate akn:docIntroducer akn:docJurisdiction akn:docNumber akn:docProponent akn:docPurpose akn:docStage akn:docStatus akn:docTitle akn:docType akn:docketNumber akn:entity akn:event akn:extractText akn:fillIn akn:from akn:heading akn:i akn:inline akn:ins akn:judge akn:lawyer akn:legislature akn:li akn:listConclusion akn:listIntroduction akn:location akn:mmod akn:mod akn:mref akn:narrative akn:neutralCitation akn:num akn:object akn:omissis akn:opinion akn:organization akn:outcome akn:p akn:party akn:person akn:placeholder akn:process akn:quantity akn:quotedText akn:recordedTime akn:ref akn:relatedDocument akn:remark akn:rmod akn:role akn:rref akn:scene akn:session akn:shortTitle akn:signature akn:span akn:sub akn:subheading akn:summary akn:sup akn:term akn:tocItem akn:u akn:vote"/>

  <!-- root template -->
  <xsl:template match="/">
    <fo:root>
      <fo:layout-master-set>
        <!-- A4 page -->
        <fo:simple-page-master master-name="A4"
                               page-width="210mm" page-height="297mm"
                               margin-top="3cm" margin-bottom="3cm"
                               margin-left="2.5cm" margin-right="2.5cm">
          <fo:region-body/>
          <fo:region-before/>
          <fo:region-after/>
        </fo:simple-page-master>
      </fo:layout-master-set>

      <!-- bookmarks / outline -->
      <fo:bookmark-tree>
        <xsl:apply-templates select="//akn:toc" mode="bookmarks"/>
      </fo:bookmark-tree>

      <!-- front matter & table of contents, Roman page numbers -->
      <!-- TODO: don't force front matter, toc to be an even number of pages -->
      <!-- TODO: skip first page number, running header -->
      <fo:page-sequence master-reference="A4" initial-page-number="1" format="i">
        <fo:static-content flow-name="xsl-region-after">
          <fo:block font-family="{$font-fam-frontmatter}" font-size="{$fontsize-frontmatter-small}" text-align="center" margin-top="1cm">
            <fo:page-number/>
          </fo:block>
        </fo:static-content>
        <fo:flow flow-name="xsl-region-body">
          <fo:block-container font-family="{$font-fam}" font-size="{$fontsize}"
                              line-height="1.3" text-align="start">
            <xsl:apply-templates select="//akn:frontMatter"/>
          </fo:block-container>
        </fo:flow>
      </fo:page-sequence>

      <!-- main body, Arabic page numbers -->
      <!-- TODO: skip first page number, running header -->
      <fo:page-sequence master-reference="A4" initial-page-number="1" format="1">
        <fo:static-content flow-name="xsl-region-before">
          <fo:block font-family="{$font-fam}"
                    font-size="{$fontsize-frontmatter-small}"
                    line-height="1.3" text-align-last="justify"
                    border-bottom-style="solid"
                    border-bottom-color="{$accent-colour}"
                    margin-top="-1.5cm">
            <fo:block start-indent="1pt" end-indent="1pt">
              <fo:inline>
                <xsl:value-of select="//akn:staticContent/akn:container[@name='running-header']/akn:span[@class='left-align']"/>
                <fo:leader leader-pattern="space"/>
                <xsl:value-of select="//akn:staticContent/akn:container[@name='running-header']/akn:span[@class='right-align']"/>
              </fo:inline>
            </fo:block>
          </fo:block>
        </fo:static-content>
        <fo:static-content flow-name="xsl-region-after">
          <fo:block font-family="{$font-fam}"
                    font-size="{$fontsize-frontmatter-small}"
                    text-align-last="justify"
                    border-top-style="solid"
                    border-top-color="{$accent-colour}"
                    margin-top="1cm" padding-top="3pt">
            <fo:block start-indent="2pt" end-indent="2pt">
              <fo:inline>
                <xsl:apply-templates select="//akn:staticContent/akn:container[@name='running-footer']/akn:span"/>
                <fo:leader leader-pattern="space"/>
                <fo:page-number/>
              </fo:inline>
            </fo:block>
          </fo:block>
        </fo:static-content>
        <fo:flow flow-name="xsl-region-body">
          <fo:block-container font-family="{$font-fam}" font-size="{$fontsize}"
                              line-height="1.3" text-align="start">
            <xsl:apply-templates/>
          </fo:block-container>
        </fo:flow>
      </fo:page-sequence>
    </fo:root>
  </xsl:template>

  <!-- the body -->

  <!-- TODO: add more / all doctypes? -->
  <xsl:template match="akn:act|akn:debate|akn:debateReport|akn:doc|akn:judgment|akn:statement">
    <fo:block>
      <xsl:apply-templates select="./*[not(self::akn:frontMatter)]"/>
    </fo:block>
  </xsl:template>

</xsl:stylesheet>
