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
					<fo:inline>
						<xsl:apply-templates select="//akn:docketNumber"/>
					</fo:inline>
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
								<fo:block></fo:block>
							</fo:table-cell>
							<fo:table-cell>
								<fo:block></fo:block>
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
								<fo:block></fo:block>
							</fo:table-cell>
							<fo:table-cell>
								<fo:block></fo:block>
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
			<fo:flow widows="2" orphans="2" flow-name="xsl-region-body">
				<xsl:apply-templates select="akn:*"/>
			</fo:flow>
		</fo:page-sequence>
	</xsl:template>
	
	<xsl:template match="akn:meta"/>
	
	<xsl:template match="akn:p">
        <fo:block>
            <xsl:apply-templates/>
        </fo:block>
    </xsl:template>
	
	<xsl:template match="akn:preface">
		<fo:block-container>
			<xsl:apply-templates/>
		</fo:block-container>
	</xsl:template>

	<xsl:template match="akn:*">
			<xsl:apply-templates/>
	</xsl:template>
	<xsl:template match="text()">
		<xsl:copy-of select="."/>
	</xsl:template>

</xsl:stylesheet>
