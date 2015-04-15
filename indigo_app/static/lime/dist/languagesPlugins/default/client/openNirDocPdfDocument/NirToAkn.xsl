<?xml version="1.0" encoding="UTF-8"?>
<!-- 
    CC-by 4.0 CIRSFID- University of Bologna
    Author: CIRSFID, University of Bologna
    Developers: Monica Palmirani, Luca Cervone, Matteo Nardi
    Contacts: monica.palmirani@unibo.it
 -->
<xsl:stylesheet version="1.0"
    xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD13"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:nir="http://www.normeinrete.it/nir/2.2/"
    xmlns:dsp="http://www.normeinrete.it/nir/disposizioni/2.2/"
    xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD13"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:h="http://www.w3.org/HTML/1998/html4"
    xmlns:cirsfid="http://www.cirsfid.unibo.it/norma/proprietario/"
    exclude-result-prefixes="xsl nir dsp xlink h akn">
    <xsl:output indent="yes"/>
    <xsl:strip-space elements="*"/>
    <xsl:namespace-alias stylesheet-prefix="akn" result-prefix="#default"/>

    <!-- Parametri dello script -->
    <xsl:param name="today"/>
    <xsl:variable name="sorgente" select="'supremaCorteDiCassazione'"/>
    <xsl:variable name="nomeSorgente" select="'Suprema Corte Di Cassazione'"/>

    <!-- Variabili usate in tutto lo script -->
    <!-- Parsing URN -->
    <xsl:variable name="urn_documento" select="substring-after(//nir:urn/@valore, 'urn:nir:')"/>
    <xsl:variable name="urn_emanante" select="substring-before($urn_documento, ':')"/>
    <xsl:variable name="urn_date" select="substring($urn_documento, string-length(substring-before($urn_documento, ';')) - 9, 10)"/>
    <xsl:variable name="urn_expression_date" select="substring-before(substring-after($urn_documento, '@'), ';')"/>
    <xsl:variable name="uri_work">
        <xsl:call-template name="convertiURN">
            <xsl:with-param name="urn" select="//nir:urn/@valore"/>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="uri_expression" select="concat($uri_work, '/ita@', $urn_date)"/>
    <xsl:variable name="uri_manifestation" select="concat($uri_expression, '/main.xml')"/>

    <!-- Radice -->
    <xsl:template match="/">
        <xsl:apply-templates select="node()"/>
    </xsl:template>

    <xsl:template match="nir:NIR">
        <akn:akomaNtoso>
            <xsl:apply-templates/>
        </akn:akomaNtoso>
    </xsl:template>

    <!-- Tipi documento -->
    <xsl:template match="nir:Legge | nir:LeggeCostituzionale | nir:DecretoLegge |
                         nir:DecretoLegislativo | nir:DecretoMinisteriale |
                         nir:RegioDecreto | nir:Dpr | nir:Dpcm | nir:LeggeRegionale |
                         nir:AttoDiAuthority | nir:DecretoMinisterialeNN |
                         nir:DprNN | nir:DpcmNN">
        <akn:act>
            <xsl:if test="//nir:mTipodoc">
                <xsl:attribute name="name">
                    <!-- TODO: Normalizza -->
                    <!-- TODO: Forse conviene fare un controllo su un dizionario -->
                    <xsl:value-of select="//nir:mTipodoc/@valore" />
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
            <xsl:call-template name="generaConclusioni" />
        </akn:act>
    </xsl:template>

    <xsl:template match="nir:DocumentoNIR | nir:Comunicato">
        <akn:doc>
            <xsl:if test="//nir:mTipodoc">
                <xsl:attribute name="name">
                    <!-- TODO: Normalizza -->
                    <!-- TODO: Forse conviene fare un controllo su un dizionario -->
                    <xsl:value-of select="//nir:mTipodoc/@valore" />
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
            <xsl:call-template name="generaConclusioni" />
        </akn:doc>
    </xsl:template>

    <xsl:template match="nir:DocArticolato | nir:SemiArticolato">
        <akn:doc>
            <xsl:text>TODO: DocArticolato/SemiArticolato</xsl:text>
        </akn:doc>
    </xsl:template>

    <!-- Meta -->
    <xsl:template match="nir:meta">
        <akn:meta>
            <xsl:call-template name="generaIdentification"/>                   <!-- Identification -->
            <xsl:apply-templates select="nir:descrittori/nir:pubblicazione"/>  <!-- Publication -->
            <xsl:apply-templates select="nir:descrittori/nir:materie"/>        <!-- Classification -->
            <xsl:call-template name="generaLifecycle"/>                        <!-- Lyfecycle -->
            <!-- Workflow -->
            <xsl:call-template name="generaAnalysis"/>                         <!-- Analysis -->
            <!-- TemporalData -->
            <xsl:call-template name="generaReferences"/>                       <!-- References -->
            <xsl:apply-templates select="nir:redazionale"/>                    <!-- Notes -->
            <xsl:apply-templates select="nir:inquadramento |                       
                                         nir:lavoripreparatori | 
                                         nir:altro | 
                                         nir:proprietario"/>                   <!-- Proprietary -->
            <!-- Presentation -->
        </akn:meta>
    </xsl:template>

    <xsl:template match="nir:inlinemeta">
        <!-- inlinemeta viene tolto dal body e spostato nel meta -->
    </xsl:template>
    
    <xsl:template name="generaIdentification">
        <akn:identification source="#{$sorgente}">
            <akn:FRBRWork>
                <akn:FRBRthis value="{$uri_work}/main"/>
                <akn:FRBRuri value="{$uri_work}"/>

                <!-- Aggiungi alias se presenti -->
                <xsl:for-each select="//nir:descrittori/nir:alias">
                    <!-- TODO: elimina name="nir" una volta che avremo la conversione -->
                    <akn:FRBRalias name="nir">
                        <xsl:attribute name="value">
                            <xsl:call-template name="convertiURN">
                                <xsl:with-param name="urn" select="@valore"/>
                            </xsl:call-template>
                        </xsl:attribute>
                    </akn:FRBRalias>
                </xsl:for-each>

                <!-- Indica la data -->
                <akn:FRBRdate name="Enactment" date="{$urn_date}"/>

                <!-- Autore -->
                <akn:FRBRauthor href="#emanante" as="#author"/>

                <!-- Nazione -->
                <akn:FRBRcountry value="it"/>

                <!-- Indica tipo documento -->
                <xsl:if test="//nir:mTipodoc">
                    <akn:FRBRname value="{//nir:mTipodoc/@valore}"/>
                </xsl:if>

                <!-- Indica se e' normativa -->
                <xsl:if test="//nir:infodoc/@normativa = 'si'">
                    <akn:FRBRprescriptive value="true"/>
                </xsl:if>
                <xsl:if test="//nir:infodoc/@normativa = 'no'">
                    <akn:FRBRprescriptive value="false"/>
                </xsl:if>

                <!-- Numero del documento -->
                <xsl:if test="//nir:mNumdoc">
                    <akn:FRBRnumber value="{//nir:mNumdoc/@valore}"/>
                </xsl:if>
            </akn:FRBRWork>

            <akn:FRBRExpression>
                <akn:FRBRthis value="{$uri_expression}/main"/>
                <akn:FRBRuri value="{$uri_expression}"/>
                <xsl:if test="$urn_expression_date">
                    <akn:FRBRdate date="{$urn_expression_date}" name=""/>
                </xsl:if>
                <xsl:if test="not($urn_expression_date)">
                    <akn:FRBRdate date="{$urn_date}" name=""/>
                </xsl:if>
                <akn:FRBRauthor href="#emanante" as="#author"/>
                <akn:FRBRlanguage language="it"/>
            </akn:FRBRExpression>

            <akn:FRBRManifestation>
                <akn:FRBRthis value="{$uri_manifestation}"/>
                <akn:FRBRuri value="{$uri_manifestation}"/>

                <!-- Redazione -->
                <akn:FRBRdate name="XMLConversion" date="{$today}"/>
                <!-- <xsl:if test="//nir:redazione[@contributo='redazione']">
                    <akn:FRBRdate name="XMLConversion" date="substring-before(current-date(), '+')">
                        <xsl:attribute name="date">
                            <xsl:call-template name="convertiData">
                                <xsl:with-param name="date"
                                    select="//nir:redazione[@contributo='redazione']/@norm"/>
                            </xsl:call-template>
                        </xsl:attribute>
                    </akn:FRBRdate>
                    <akn:FRBRauthor href="#redazione" as="#editor"/>
                </xsl:if> -->
                <akn:FRBRauthor href="#cirsfid"/>

                <xsl:if test="//nir:redazione[@contributo='editor']">
                    <akn:preservation>
                        <cirsfid:software value="{//nir:redazione[@contributo='editor']/@nome}"/>
                        <cirsfid:affiliation value="{//nir:redazione[@contributo='editor']/@url}"/>
                    </akn:preservation>
                </xsl:if>
            </akn:FRBRManifestation>
        </akn:identification>
    </xsl:template>

    <xsl:template name="generaLifecycle">
        <!-- Nella convertire del lifecycle gli id vengono mantenuti -->
        <akn:lifecycle source="#{$sorgente}">
            <xsl:for-each select="//nir:ciclodivita/nir:eventi/nir:evento">
                <akn:eventRef eId="{@id}" source="{@fonte}">
                    <xsl:attribute name="date">
                        <xsl:call-template name="convertiData">
                            <xsl:with-param name="date" select="@data"/>
                        </xsl:call-template>
                    </xsl:attribute>
                    <!-- Todo: il mappaggio va completato -->
                    <xsl:if test="@tipo = 'originale'">
                        <xsl:attribute name="type"><xsl:text>generation</xsl:text></xsl:attribute>
                    </xsl:if>
                    <xsl:if test="@tipo = 'modifica'">
                        <xsl:attribute name="type"><xsl:text>amendment</xsl:text></xsl:attribute>
                    </xsl:if>
                </akn:eventRef>
            </xsl:for-each>

            <!-- Nel caso manchi nir:ciclodivita, inseriamo noi l'evento crazione -->
            <xsl:if test="not(//nir:ciclodivita/nir:eventi/nir:evento/@tipo='originale')">
                <akn:eventRef eId="genEvnt" source="#genRef" type="generation">
                    <xsl:attribute name="date">
                        <xsl:call-template name="convertiData">
                            <xsl:with-param name="date" select="//nir:entratainvigore/@norm"/>
                        </xsl:call-template>
                    </xsl:attribute>
                </akn:eventRef>
            </xsl:if>
        </akn:lifecycle>
    </xsl:template>

    <xsl:template name="generaReferences">
        <akn:references source="#{$sorgente}">
            <!-- Reference a documento originale -->
            <xsl:for-each select="//nir:ciclodivita//nir:originale">
                <akn:original eId="{@id}" showAs="">
                    <xsl:attribute name="href">
                        <xsl:call-template name="convertiURN">
                            <xsl:with-param name="urn" select="@xlink:href"/>
                        </xsl:call-template>
                    </xsl:attribute>
                </akn:original>
            </xsl:for-each>

            <!-- Nel caso manchi nir:ciclodivita, inseriamo noi l'evento crazione -->
            <xsl:if test="not(//nir:ciclodivita//nir:originale)">
                <akn:original eId="genRef" showAs="" href="{$uri_work}"/>
            </xsl:if>

            <!-- Reference a modifiche attive -->
            <xsl:for-each select="//nir:ciclodivita//nir:attiva">
                <akn:activeRef eId="{@id}" showAs="">
                    <xsl:attribute name="href">
                        <xsl:call-template name="convertiURN">
                            <xsl:with-param name="urn" select="@xlink:href"/>
                        </xsl:call-template>
                    </xsl:attribute>
                </akn:activeRef>
            </xsl:for-each>

            <!-- Reference a modifiche passive -->
            <xsl:for-each select="//nir:ciclodivita//nir:passiva">
                <akn:passiveRef eId="{@id}" showAs="">
                    <xsl:attribute name="href">
                        <xsl:call-template name="convertiURN">
                            <xsl:with-param name="urn" select="@xlink:href"/>
                        </xsl:call-template>
                    </xsl:attribute>
                </akn:passiveRef>
            </xsl:for-each>

            <!-- Reference a sorgente documento -->
            <akn:TLCOrganization eId="{$sorgente}" href="/ontology/organizations/it/{$sorgente}" showAs="{$nomeSorgente}"/>

            <!-- Reference all'emanante -->
            <xsl:variable name="smallcase" select="'abcdefghijklmnopqrstuvwxyz'"/>
            <xsl:variable name="uppercase" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>
            <xsl:variable name="amanante">
                <xsl:if test="//nir:mEmanante">
                    <xsl:value-of select="//nir:mEmanante/@valore"/>
                </xsl:if>
                <xsl:if test="not(//nir:mEmanante)">
                    <xsl:value-of select="$urn_emanante"/>
                </xsl:if>
            </xsl:variable>
            <xsl:variable name="idEmanante" select="concat(
                translate(substring($amanante, 1, 1), $smallcase, $uppercase),
                translate(substring($amanante, 2), ' ', '_')
            )"/>
            <akn:TLCOrganization eId="emanante" href="/ontology/organizations/it/{$idEmanante}" showAs="{$amanante}"/>

            <!-- Redazione -->
            <xsl:if test="//nir:redazione[@contributo='redazione']">
                <akn:TLCOrganization eId="redazione" href="{//nir:redazione[@contributo='redazione']/@url}" 
                    showAs="{//nir:redazione[@contributo='redazione']/@nome}"/>
            </xsl:if>

            <!-- Allegati -->
            <xsl:for-each select="//nir:haallegato">
                <akn:hasAttachment href="{@xlink:href}" showAs=""/>
            </xsl:for-each>
            <xsl:for-each select="//nir:allegatodi">
                <akn:attachmentOf href="{@xlink:href}" showAs=""/>
            </xsl:for-each>

            <!-- Giurisprudenza -->
            <xsl:for-each select="//nir:giurisprudenza">
                <akn:jurisprudence href="{@xlink:href}" showAs=""/>
            </xsl:for-each>

            <!-- Firme -->
            <xsl:for-each select="//nir:firma">
                <xsl:if test="not(@tipo=preceding::nir:firma/@tipo)">
                    <akn:TLCConcept eId="{@tipo}" href="/ontology/concepts/it/{@tipo}" showAs="{@tipo}"/>
                </xsl:if>
            </xsl:for-each>

            <!-- Cirsfid -->
            <akn:TLCOrganization eId="cirsfid" href="http://www.cirsfid.unibo.it/" showAs="CIRSFID"/>

            <!-- Riferimenti esterni -->

            <!-- A quanto pare non e' necessario (e c'era un bug nella numerazione)
            <xsl:for-each select="//nir:rif">
                <xsl:variable name="href" select="@xlink:href"/>
                <xsl:variable name="n" select="count(./preceding::nir:rif[@xlink:href != $href])+1"/>
                <xsl:if test="not(./preceding::nir:rif[@xlink:href = $href])">
                    <akn:TLCReference eId="rif{$n}" showAs="">
                        <xsl:attribute name="href">
                            <xsl:call-template name="convertiURN">
                                <xsl:with-param name="urn" select="@xlink:href"/>
                            </xsl:call-template>
                        </xsl:attribute>
                    </akn:TLCReference>
                </xsl:if>
            </xsl:for-each>

            <xsl:for-each select="//nir:irif">
                <xsl:variable name="href" select="@xlink:href"/>
                <xsl:variable name="start" select="count(./preceding::nir:irif[@xlink:href != $href])+1"/>
                <xsl:variable name="finoa" select="@finoa"/>
                <xsl:variable name="end" select="count(./preceding::nir:irif[@finoa != $finoa])+1"/>
                <xsl:if test="not(./preceding::nir:irif[@xlink:href = $href])">
                    <akn:TLCReference eId="irif_s{$start}" showAs="">
                        <xsl:attribute name="href">
                            <xsl:call-template name="convertiURN">
                                <xsl:with-param name="urn" select="@xlink:href"/>
                            </xsl:call-template>
                        </xsl:attribute>
                    </akn:TLCReference>
                </xsl:if>
                <xsl:if test="not(./preceding::nir:irif[@finoa = $finoa])">
                    <akn:TLCReference eId="irif_e{$end}" showAs="">
                        <xsl:attribute name="href">
                            <xsl:call-template name="convertiURN">
                                <xsl:with-param name="urn" select="@finoa"/>
                            </xsl:call-template>
                        </xsl:attribute>
                    </akn:TLCReference>
                </xsl:if>
            </xsl:for-each> -->
        </akn:references>
    </xsl:template>

    <xsl:template match="nir:descrittori/nir:pubblicazione">
        <akn:publication>
            <xsl:if test="@norm">
                <xsl:attribute name="date">
                    <xsl:call-template name="convertiData">
                        <xsl:with-param name="date" select="@norm"/>
                    </xsl:call-template>
                </xsl:attribute>
            </xsl:if>
            <xsl:attribute name="name">
                <xsl:value-of select="@tipo"/>
            </xsl:attribute>
            <xsl:if test="@tipo='GU'">
                <xsl:attribute name="showAs">Gazzetta Ufficiale</xsl:attribute>
            </xsl:if>
            <xsl:if test="@num">
                <xsl:attribute name="number">
                    <xsl:value-of select="@num"/>
                </xsl:attribute>
            </xsl:if>
        </akn:publication>
    </xsl:template>

    <xsl:template match="nir:descrittori/nir:materie">
        <akn:classification source="#{$sorgente}">
            <xsl:for-each select="nir:materia">
                <akn:keyword dictionary="#tesauroCassazione" showAs="{@valore}" value="{@valore}"/>
            </xsl:for-each>
        </akn:classification>
    </xsl:template>

    <xsl:template match="nir:inquadramento">
        <xsl:if test="nir:oggetto">
            <akn:proprietary source="#{$sorgente}">
                <cirsfid:oggetto>
                    <xsl:for-each select="nir:oggetto/*">
                        <xsl:element name="cirsfid:{name()}">
                            <xsl:attribute name="valore">
                                <xsl:value-of select="@valore"/>
                            </xsl:attribute>
                        </xsl:element>
                    </xsl:for-each>
                </cirsfid:oggetto>
            </akn:proprietary>
        </xsl:if>
        <xsl:if test="nir:proponenti">
            <akn:proprietary source="#{$sorgente}">
                <cirsfid:proponenti>
                    <xsl:for-each select="nir:proponenti/*">
                        <xsl:element name="cirsfid:{name()}">
                            <xsl:attribute name="valore">
                                <xsl:value-of select="@valore"/>
                            </xsl:attribute>
                        </xsl:element>
                    </xsl:for-each>
                </cirsfid:proponenti>
            </akn:proprietary>
        </xsl:if>
    </xsl:template>

    <xsl:template match="nir:lavoripreparatori | nir:altro | nir:proprietario">
        <akn:proprietary>
            <xsl:attribute name="source">
                <xsl:value-of select="$sorgente"/>
            </xsl:attribute>
            <xsl:apply-templates select="." mode="copyEverything"/>
        </akn:proprietary>
    </xsl:template>

    <xsl:template match="nir:redazionale">
        <xsl:if test="nir:nota">
            <akn:notes>
                <xsl:attribute name="source">
                    <xsl:value-of select="$sorgente"/>
                </xsl:attribute>
                <xsl:for-each select="nir:nota">
                    <akn:note eId="{@id}">
                        <xsl:apply-templates select="*"/>
                    </akn:note>
                </xsl:for-each>
            </akn:notes>
        </xsl:if>
        <xsl:if test="nir:altro">
            <akn:proprietary>
                <xsl:attribute name="source">
                    <xsl:value-of select="$sorgente"/>
                </xsl:attribute>
                <xsl:apply-templates select="nir:altro/node()" mode="copyEverything"/>
            </akn:proprietary>
        </xsl:if>
    </xsl:template>

    <xsl:template match="nir:risoluzioni">
        <xsl:for-each select="nir:risoluzione">
            <!-- TODO -->
        </xsl:for-each>
    </xsl:template>

    <xsl:template name="generaAnalysis">
        <akn:analysis source="#{$sorgente}">
            <xsl:if test="//nir:modificheattive">
                <akn:activeModifications>
                    <!-- Todo: genera id? -->
                    <xsl:apply-templates select="//nir:modificheattive"/>
                </akn:activeModifications>
            </xsl:if>
            <xsl:if test="//nir:modifichepassive">
                <akn:passiveModifications>
                    <!-- Todo: genera id? -->
                    <xsl:apply-templates select="//nir:modifichepassive"/>
                </akn:passiveModifications>
            </xsl:if>
            <xsl:apply-templates select="//nir:regole"/>
        </akn:analysis>
    </xsl:template>

    <xsl:template match="dsp:norma">
        <akn:destination>
            <xsl:choose>
                <xsl:when test="dsp:subarg/cirsfid:sub">
                    <xsl:attribute name="href">
                        <xsl:call-template name="convertiURN">
                            <xsl:with-param name="urn" select="dsp:subarg/cirsfid:sub[1]/@xlink:href"/>
                        </xsl:call-template>
                    </xsl:attribute>
                </xsl:when>
                <xsl:when test="dsp:pos">
                    <xsl:attribute name="href">
                        <xsl:call-template name="convertiURN">
                            <xsl:with-param name="urn" select="dsp:pos/@xlink:href"/>
                        </xsl:call-template>
                    </xsl:attribute>
                    <xsl:attribute name="pos">
                        <xsl:text>unspecified</xsl:text>
                    </xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:attribute name="href">
                        <xsl:call-template name="convertiURN">
                            <xsl:with-param name="urn" select="@xlink:href"/>
                        </xsl:call-template>
                    </xsl:attribute>
                </xsl:otherwise>
            </xsl:choose>
        </akn:destination>
    </xsl:template>

    <xsl:template match="dsp:termine      | dsp:condizione    | dsp:posizione   |
                         
                         dsp:visto        | dsp:sentito       | dsp:considerato |
                         dsp:suproposta   | dsp:basegiuridica | dsp:proposta    | 
                         dsp:parere       | dsp:richiesta     | dsp:procedura   |
                         dsp:considerando | dsp:motivazione   | dsp:finalita    |
                         dsp:finanziaria  | dsp:ambito        | dsp:metaregola  |
                         dsp:definitoria  | dsp:istitutiva    |dsp:organizzativa|
                         dsp:status       | dsp:competenza    | dsp:delega      |
                         dsp:revoca       | dsp:diritto       | dsp:dovere      |
                         dsp:pretesa      | dsp:obbligo       | dsp:divieto     |
                         dsp:permesso     | dsp:procedimento  | dsp:sanzione    |
                         dsp:riparazione  | dsp:informazione  | dsp:regola      |

                         dsp:soggetto     | dsp:effetto       | dsp:partizione  |
                         dsp:tiporegola   | dsp:fatto         | dsp:organo      | 
                         dsp:fine         | dsp:destinatario  | dsp:territorio  | 
                         dsp:attivita     | dsp:definiendum   | dsp:definiens   | 
                         dsp:qualifica    | dsp:delegante     | dsp:controparte | 
                         dsp:azione       | dsp:pena          |

                         nir:regole">
        <!-- <akn:proprietary>
            <xsl:apply-templates select="." mode="copyEverything"/>
        </akn:proprietary> -->
    </xsl:template>

    <xsl:template match="nir:modificheattive/*/dsp:pos | nir:modifichepassive/*/dsp:pos">
        <xsl:variable name="oId" select="substring-after(@xlink:href, '#')"/>
        <akn:source>
            <xsl:attribute name="href">#<xsl:apply-templates mode="genera_id" select="//node()[@id = $oId]"/></xsl:attribute>
            <xsl:apply-templates />
        </akn:source>
    </xsl:template>

    <xsl:template match="dsp:abrogazione">
        <akn:textualMod type="repeal">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:textualMod>
    </xsl:template>

    <xsl:template match="dsp:sostituzione">
        <akn:textualMod type="substitution">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:textualMod>
    </xsl:template>

    <xsl:template match="dsp:integrazione">
        <akn:textualMod type="insertion">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:textualMod>
    </xsl:template>

    <xsl:template match="dsp:ricollocazione">
        <akn:textualMod type="renumbering">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:textualMod>
    </xsl:template>

    <xsl:template match="dsp:intautentica">
        <akn:meaningMod type="authenticInterpretation">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:meaningMod>
    </xsl:template>

    <xsl:template match="dsp:variazione">
        <akn:meaningMod type="variation">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:meaningMod>
    </xsl:template>

    <xsl:template match="dsp:modtermini">
        <akn:meaningMod type="termModification">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:meaningMod>
    </xsl:template>

    <xsl:template match="dsp:vigenza">
        <akn:forceMod type="entryIntoForce">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:forceMod>
    </xsl:template>

    <xsl:template match="dsp:annullamento">
        <akn:forceMod type="uncostitutionality">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:forceMod>
    </xsl:template>

    <xsl:template match="dsp:proroga">
        <akn:efficacyMod type="prorogationOfEfficacy">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:efficacyMod>
    </xsl:template>

    <xsl:template match="dsp:reviviscenza">
    </xsl:template>

    <xsl:template match="dsp:retroattivita">
        <akn:efficacyMod type="retroactivity">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:efficacyMod>
    </xsl:template>

    <xsl:template match="dsp:ultrattivita">
        <akn:efficacyMod type="extraEfficacy">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:efficacyMod>
    </xsl:template>

    <xsl:template match="dsp:inapplicazione">
        <akn:efficacyMod type="inapplication">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:efficacyMod>
    </xsl:template>

    <xsl:template match="dsp:deroga">
        <akn:scopeMod type="exceptionOfScope" incomplete="true">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:scopeMod>
    </xsl:template>

    <xsl:template match="dsp:estensione">
        <akn:scopeMod type="extensionOfScope">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:scopeMod>
    </xsl:template>

    <xsl:template match="dsp:estensione">
        <akn:scopeMod type="extensionOfScope" incomplete="true">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:scopeMod>
    </xsl:template>

    <xsl:template match="dsp:recepisce">
        <akn:legalSystemMod type="application">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:legalSystemMod>
    </xsl:template>

    <xsl:template match="dsp:attua">
        <akn:legalSystemMod type="implementation">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:legalSystemMod>
    </xsl:template>

    <xsl:template match="dsp:ratifica">
        <akn:legalSystemMod type="ratification">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:legalSystemMod>
    </xsl:template>

    <xsl:template match="dsp:attuadelega">
        <akn:legalSystemMod type="legislativeDelegation">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:legalSystemMod>
    </xsl:template>

    <xsl:template match="dsp:attuadelegifica">
        <akn:legalSystemMod type="deregulation">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:legalSystemMod>
    </xsl:template>

    <xsl:template match="dsp:converte">
        <akn:legalSystemMod type="conversion">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:legalSystemMod>
    </xsl:template>

    <xsl:template match="dsp:reitera">
        <akn:legalSystemMod type="reiteration">
            <xsl:apply-templates select="./dsp:*[not(name() = 'dsp:novella') and not(name() = 'dsp:novellando')]"/>
            <xsl:apply-templates select="dsp:novellando"/>
            <xsl:apply-templates select="dsp:novella"/>
        </akn:legalSystemMod>
    </xsl:template>

    <xsl:template match="dsp:modifica">
    </xsl:template>

    <xsl:template match="dsp:decadimento">
        <akn:legalSystemMod type="expiration">
            <xsl:apply-templates />
        </akn:legalSystemMod>
    </xsl:template>

    <xsl:template match="dsp:novella">
        <xsl:variable name="oId" select="substring-after(dsp:pos/@xlink:href, '#')"/>
        <akn:new>
            <xsl:attribute name="href">
                <xsl:apply-templates mode="genera_id" select="//node()[@id = $oId]"/>
            </xsl:attribute>
            <xsl:apply-templates />
        </akn:new>
    </xsl:template>

    <xsl:template match="dsp:novellando">
        <xsl:variable name="oId" select="substring-after(dsp:pos/@xlink:href, '#')"/>
        <akn:old>
            <xsl:attribute name="href">
                <xsl:apply-templates mode="genera_id" select="//node()[@id = $oId]"/>
            </xsl:attribute>
            <xsl:apply-templates />
        </akn:old>
    </xsl:template>

    <!-- Intestazione -->
    <xsl:template match="nir:intestazione">
        <akn:preface>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <akn:p>
                <xsl:apply-templates select="node() | @*"/>
            </akn:p>
        </akn:preface>
    </xsl:template>

    <xsl:template match="nir:intestazione//nir:tipoDoc">
        <akn:docType>
            <xsl:apply-templates/>
        </akn:docType>
    </xsl:template>

    <xsl:template match="nir:intestazione//nir:numDoc">
        <akn:docNumber>
            <xsl:apply-templates/>
        </akn:docNumber>
    </xsl:template>

    <xsl:template match="nir:intestazione//nir:titoloDoc">
        <akn:docTitle>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:apply-templates/>
            <xsl:if test=". = //nir:titoloDoc[1]">
                <xsl:for-each select="//nir:avvertenza">
                    <akn:authorialNote>
                        <xsl:apply-templates/>
                    </akn:authorialNote>
                </xsl:for-each>
            </xsl:if>
        </akn:docTitle>
    </xsl:template>

    <xsl:template match="nir:intestazione//nir:emanante">
        <akn:docAuthority>
            <xsl:apply-templates/>
        </akn:docAuthority>
    </xsl:template>

    <xsl:template match="nir:intestazione//nir:dataDoc">
        <akn:docDate>
            <xsl:apply-templates select="*|@*"/>
        </akn:docDate>
    </xsl:template>

    <xsl:template match="nir:intestazione//nir:dataDoc/@norm">
        <xsl:attribute name="date">
            <xsl:call-template name="convertiData">
                <xsl:with-param name="date" select="."/>
            </xsl:call-template>
        </xsl:attribute>
    </xsl:template>

    <!-- Preambolo -->
    <xsl:template match="nir:formulainiziale">
        <akn:preamble>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:choose>
                <xsl:when test="nir:preambolo">
                    <akn:p>
                        <xsl:apply-templates select="nir:preambolo/preceding-sibling::node()"/>
                    </akn:p>
                    <xsl:apply-templates select="nir:preambolo"/>
                    <akn:p>
                        <xsl:apply-templates select="nir:preambolo/following-sibling::node()"/>
                    </akn:p>                    
                </xsl:when>
                <xsl:otherwise>
                    <akn:p>
                        <xsl:apply-templates />
                    </akn:p>
                </xsl:otherwise>
            </xsl:choose>
        </akn:preamble>
    </xsl:template>

    <xsl:template match="nir:preambolo">
        <akn:container name="preambolo_nir">
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:apply-templates />
        </akn:container>
    </xsl:template>

    <!-- Articolato -->
    <xsl:template match="nir:articolato">
        <xsl:choose>
            <xsl:when test="//nir:DocumentoNIR  | //nir:Comunicato |
                            //nir:DocArticolato | //nir:SemiArticolato">
                <akn:mainBody>
                    <xsl:apply-templates/>
                </akn:mainBody>
            </xsl:when>
            <xsl:otherwise>
                <akn:body>
                    <xsl:apply-templates/>
                </akn:body>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- Conclusione -->
    <xsl:template match="nir:formulafinale | nir:conclusione">
        <!-- Vengono gia' gestisti in generaConclusioni -->
    </xsl:template>

    <xsl:template name="generaConclusioni">
        <xsl:if test="//nir:conclusione | //nir:formulafinale">
            <akn:conclusions>
                <xsl:apply-templates select="//nir:conclusione | //nir:formulafinale" mode="conclusioni"/>
            </akn:conclusions>
        </xsl:if>
    </xsl:template>
    
    <xsl:template match="nir:formulafinale" mode="conclusioni">
        <akn:container name="formulafinale" eId="comp1-sgn1" class="right">
            <akn:p>
                <xsl:apply-templates/>
            </akn:p>
        </akn:container>
    </xsl:template>
    
    <xsl:template match="nir:conclusione" mode="conclusioni">
        <akn:p><xsl:apply-templates/></akn:p>
    </xsl:template>

    <!-- Conversione elementi interni e gerarchia -->
    <xsl:template match="nir:decorazione/nir:rango">
        <akn:decoration>
            <xsl:copy-of select="@tipo"/>
        </akn:decoration>
    </xsl:template>

    <xsl:template match="nir:libro">
        <akn:book>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:apply-templates/>
        </akn:book>
    </xsl:template>

    <xsl:template match="nir:parte">
        <akn:part>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:apply-templates/>
        </akn:part>
    </xsl:template>

    <xsl:template match="nir:titolo">
        <akn:title>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:apply-templates/>
        </akn:title>
    </xsl:template>

    <xsl:template match="nir:capo">
        <akn:chapter>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:apply-templates/>
        </akn:chapter>
    </xsl:template>

    <xsl:template match="nir:sezione">
        <akn:section>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:apply-templates/>
        </akn:section>
    </xsl:template>

    <xsl:template match="nir:paragrafo">
        <akn:paragraph>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:apply-templates select="node()"/>
        </akn:paragraph>
    </xsl:template>

    <xsl:template match="nir:articolo">
        <akn:article>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:apply-templates select="node()"/>
        </akn:article>
    </xsl:template>

    <xsl:template match="nir:rubrica">
        <!-- Come scelgo se mettere subheading? -->
        <akn:heading>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:apply-templates/>
        </akn:heading>
    </xsl:template>

    <xsl:template match="nir:num">
        <akn:num>
            <xsl:apply-templates/>
        </akn:num>
    </xsl:template>

    <xsl:template match="nir:comma">
        <akn:paragraph>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:apply-templates select="node()"/>
        </akn:paragraph>
    </xsl:template>

    <xsl:template match="nir:el[name(./preceding-sibling::node()[1]) != 'el'] |
                         nir:en[name(./preceding-sibling::node()[1]) != 'en'] |
                         nir:ep[name(./preceding-sibling::node()[1]) != 'ep']">
        <akn:list>
            <xsl:variable name="current" select="."/>
            <xsl:for-each select="following-sibling::node()[name() = name($current)]">
                <akn:point>
                    <xsl:apply-templates select="." mode="genera_eId"/>
                    <xsl:apply-templates select="node()"/>
                </akn:point>
            </xsl:for-each>
        </akn:list>
    </xsl:template>

    <xsl:template match="nir:el | nir:en | nir:ep">
    </xsl:template>

    <xsl:template match="nir:corpo">
        <akn:content>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <akn:p>
                <xsl:apply-templates/>
            </akn:p>
        </akn:content>
    </xsl:template>

    <xsl:template match="nir:alinea">
        <akn:intro>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <akn:p>
                <xsl:apply-templates/>
            </akn:p>
        </akn:intro>
    </xsl:template>

    <xsl:template match="nir:coda">
        <akn:wrapUp>
            <akn:p>
                <xsl:apply-templates/>
            </akn:p>
        </akn:wrapUp>
    </xsl:template>

    <xsl:template match="nir:dataeluogo">
        <akn:date>
            <xsl:attribute name="date">
                <xsl:call-template name="convertiData">
                    <xsl:with-param name="date" select="@norm"/>
                </xsl:call-template>
            </xsl:attribute>
            <xsl:apply-templates select="node()"/>
        </akn:date>
    </xsl:template>

    <xsl:template match="nir:firma">
        <akn:signature refersTo="#{@tipo}">
            <xsl:apply-templates select="node()"/>
        </akn:signature>
    </xsl:template>

    <xsl:template match="nir:annessi">
        <akn:attachments>
            <xsl:apply-templates/>
        </akn:attachments>
    </xsl:template>

    <xsl:template match="nir:elencoAnnessi">
        <!-- Non serve in Akomantoso -->
    </xsl:template>

    <xsl:template match="nir:annesso">
        <!-- TODO: qui c'e' molto da fare 
        <akn:attachments>
            <xsl:apply-templates/>
        </akn:attachments>
        -->
    </xsl:template>

    <xsl:template match="nir:rif">
        <akn:ref>
            <xsl:attribute name="href">
                <xsl:call-template name="convertiURN">
                    <xsl:with-param name="urn" select="@xlink:href"/>
                </xsl:call-template>
            </xsl:attribute>
            <xsl:apply-templates select="node()"/>
        </akn:ref>
    </xsl:template>

    <xsl:template match="nir:mrif">
        <akn:mref>
            <xsl:apply-templates select="node()"/>
        </akn:mref>
    </xsl:template>

    <xsl:template match="nir:irif">
        <akn:rref>
            <xsl:attribute name="from">
                <xsl:call-template name="convertiURN">
                    <xsl:with-param name="urn" select="@xlink:href"/>
                </xsl:call-template>
            </xsl:attribute>
            <xsl:attribute name="upTo">
                <xsl:call-template name="convertiURN">
                    <xsl:with-param name="urn" select="@finoa"/>
                </xsl:call-template>
            </xsl:attribute>
            <xsl:apply-templates/>
        </akn:rref>
    </xsl:template>

    <xsl:template match="nir:mod">
        <akn:mod>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:apply-templates/>
        </akn:mod>
    </xsl:template>

    <xsl:template match="nir:mmod">
        <akn:mmod>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:apply-templates/>
        </akn:mmod>
    </xsl:template>

    <xsl:template match="nir:imod">
        <akn:rmod>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:attribute name="from">
                <xsl:call-template name="convertiURN">
                    <xsl:with-param name="urn" select="@xlink:href"/>
                </xsl:call-template>
            </xsl:attribute>
            <xsl:attribute name="upTo">
                <xsl:call-template name="convertiURN">
                    <xsl:with-param name="urn" select="@finoa"/>
                </xsl:call-template>
            </xsl:attribute>
            <xsl:apply-templates/>
        </akn:rmod>
    </xsl:template>

    <xsl:template match="nir:virgolette">
        <xsl:choose>
            <xsl:when test="@tipo = 'struttura'">
                <akn:quotedStructure>
                    <xsl:apply-templates select="." mode="genera_eId"/>
                    <xsl:apply-templates select="node()"/>
                </akn:quotedStructure>
            </xsl:when>
            <xsl:otherwise>
                <akn:quotedText>
                    <xsl:apply-templates select="." mode="genera_eId"/>
                    <xsl:apply-templates select="node()"/>
                </akn:quotedText>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="nir:virgolette[@tipo = 'struttura']/text()">
        <xsl:if test="position() = 1">
            <xsl:attribute name="startQuote">
                <xsl:value-of select="."/>
            </xsl:attribute>
            <xsl:attribute name="endQuote">
                <xsl:value-of select="following-sibling::text()[last()]"/>
            </xsl:attribute>
        </xsl:if>
    </xsl:template>

    <xsl:template match="nir:def">
        <akn:def>
            <xsl:apply-templates/>
        </akn:def>
    </xsl:template>

    <xsl:template match="nir:atto">
        <akn:proprietary source="#{$sorgente}">
            <cirsfid:atto>
                <xsl:apply-templates/>
            </cirsfid:atto>
        </akn:proprietary>
    </xsl:template>

    <xsl:template match="nir:data">
        <akn:date>
            <xsl:attribute name="date">
                <xsl:call-template name="convertiData">
                    <xsl:with-param name="date" select="@norm"/>
                </xsl:call-template>
            </xsl:attribute>
            <xsl:apply-templates/>
        </akn:date>
    </xsl:template>

    <xsl:template match="nir:soggetto">
        <akn:person>
            <xsl:apply-templates/>
        </akn:person>
    </xsl:template>

    <xsl:template match="nir:ente">
        <!-- Come uso @codice? -->
        <akn:organization>
            <xsl:apply-templates/>
        </akn:organization>
    </xsl:template>

    <xsl:template match="nir:luogo">
        <!-- Come uso @dove? -->
        <akn:location>
            <xsl:apply-templates/>
        </akn:location>
    </xsl:template>

    <xsl:template match="nir:importo">
        <akn:quantity>
            <xsl:apply-templates/>
        </akn:quantity>
    </xsl:template>

    <xsl:template match="nir:ndr">
        <akn:noteRef href="{@num}">
            <xsl:apply-templates select="node()"/>
        </akn:noteRef>
    </xsl:template>

    <xsl:template match="nir:vuoto">
        <akn:omissis>
            <xsl:apply-templates/>
        </akn:omissis>
    </xsl:template>

    <xsl:template match="nir:inlinea">
        <akn:inline>
            <xsl:apply-templates/>
        </akn:inline>
    </xsl:template>

    <xsl:template match="nir:blocco">
        <akn:block>
            <xsl:apply-templates/>
        </akn:block>
    </xsl:template>

    <xsl:template match="nir:contenitore">
        <akn:container name="{@nome}">
            <xsl:apply-templates/>
        </akn:container>
    </xsl:template>
    
    <xsl:template match="nir:DocumentoNIR/nir:contenitore">
        <akn:mainBody>
            <akn:container name="{@nome}">
                <xsl:apply-templates/>
            </akn:container>
        </akn:mainBody>
    </xsl:template>

    <xsl:template match="nir:partizione">
    </xsl:template>

    <xsl:template match="nir:lista">
        <akn:blockList>
            <xsl:apply-templates select="." mode="genera_eId"/>
            <xsl:apply-templates/>
        </akn:blockList>
    </xsl:template>

    <xsl:template match="nir:gerarchia">
        <akn:mainBody>
            <xsl:apply-templates/>
        </akn:mainBody>
    </xsl:template>

    <xsl:template match="nir:l1 | nir:l2 | nir:l3 | nir:l4 | nir:l5 | nir:l6 | nir:l7 | nir:l8 | nir:l9">
        <akn:hcontainer>
            <xsl:apply-templates/>
        </akn:hcontainer>
    </xsl:template>

    <xsl:template match="nir:tit">
    </xsl:template>

    <!-- Conversione HTML -->
    <xsl:template match="h:*">
        <!-- Gli elementi HTML restano uguali, cambia solo il namespace -->
        <xsl:element name="akn:{local-name()}">
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="h:br">
        <akn:eol>
            <xsl:apply-templates />
        </akn:eol>
    </xsl:template>
    
    <xsl:template match="h:p[text() = 'omissis']">
        <akn:p>
            <akn:omissis>
                <xsl:apply-templates/>
            </akn:omissis>
        </akn:p>
    </xsl:template>

    <!-- Funzioni ausiliari -->
    <xsl:template match="*" mode="genera_eId">
        <xsl:attribute name="eId">
            <xsl:apply-templates select="." mode="genera_id"/>
        </xsl:attribute>
    </xsl:template>

    <xsl:template match="*" mode="genera_id">
        <xsl:variable name="current" select="."/>
        <xsl:for-each select="./ancestor-or-self::node()
            [(name() = 'virgolette' and @tipo = 'struttura') or 
             (name() = 'virgolette' and @tipo = 'parola') or 
             (name() = 'articolo') or
             (name() = 'capo') or
             (name() = 'alinea') or
             (name() = 'list') or
             (name() = 'paragrafo' or name() = 'comma') or
             (name() = 'sezione') or
             (name() = 'rubrica') or
             (name() = 'intestazione') or
             (name() = 'preambolo') or
             (name() = 'formulainiziale') or
             (name() = 'libro') or
             (name() = 'parte') or
             (name() = 'titolo') or
             (name() = 'corpo') or
             (name() = 'mod') or
             (name() = 'mmod') or
             (name() = 'preambolo') or
             (name() = 'titoloDoc') or
             (name() = 'el' or name() = 'en' or name() = 'ep') or
             (name() = 'imod')]">

            <xsl:choose>
                <xsl:when test="name() = 'virgolette' and @tipo = 'struttura'">
                    <xsl:text>qstr</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'virgolette' and @tipo = 'parola'">
                    <xsl:text>Qtxt</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'articolo'">
                    <xsl:text>art</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'capo'">
                    <xsl:text>chp</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'alinea'">
                    <xsl:text>intro</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'list'">
                    <xsl:text>list</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'paragrafo' or name() = 'comma'">
                    <xsl:text>para</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'sezione'">
                    <xsl:text>Sec</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'rubrica'">
                    <xsl:text>hdg</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'intestazione'">
                    <xsl:text>preface</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'formulainiziale'">
                    <xsl:text>preamble</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'libro'">
                    <xsl:text>book</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'parte'">
                    <xsl:text>part</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'titolo'">
                    <xsl:text>title</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'corpo'">
                    <xsl:text>content</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'mod'">
                    <xsl:text>mod</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'mmod'">
                    <xsl:text>mmod</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'imod'">
                    <xsl:text>rmod</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'titoloDoc'">
                    <xsl:text>docTitle</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'preambolo'">
                    <xsl:text>preambolonir</xsl:text>
                </xsl:when>
                <xsl:when test="name() = 'el' or name() = 'en' or name() = 'ep'">
                    <xsl:text>point</xsl:text>
                </xsl:when>
                <xsl:otherwise><xsl:text>error</xsl:text></xsl:otherwise>
            </xsl:choose>

            <xsl:text>_</xsl:text>
            <xsl:variable name="name" select="name()"/>
            <xsl:value-of select="count(. | ./preceding-sibling::node()[name() = $name])"/>

            <xsl:if test=". != $current">
                <xsl:text>__</xsl:text>
            </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <xsl:template name="convertiData">
        <xsl:param name="date"/>
        <xsl:variable name="year" select="substring($date, 1, 4)"/>
        <xsl:variable name="month" select="substring($date, 5, 2)"/>
        <xsl:variable name="day" select="substring($date, 7, 2)"/>
        <xsl:value-of select="concat($year, '-', $month, '-', $day)"/>
    </xsl:template>

    <xsl:template name="convertiURN">
        <!--
            nir       urn:nir:autorita:provvedimento:estremi[:annesso..][@versione][*comunicato..][$manifestazione][#id]
                      urn:nir:presidenza.consiglio.ministri:decreto:2009-12-18;206
            akn       /akn/it/act/provvedimento/autorita/data/num_title/ita@
            example   urn:nir:stato:decreto.legislativo:1992-04-30;285#art118-com6
        -->
        <xsl:param name="urn"/>
        <xsl:variable name="i1" select="substring-after($urn, 'urn:nir:')"/>
        <!-- Eg. autorita:provvedimento:estremi[:annesso..][@versione][*comunicato..][$manifestazione][#id] -->
        <xsl:variable name="autorita" select="substring-before($i1, ':')"/>
        <!-- Eg. autorita -->
        <xsl:variable name="i2" select="substring-after($i1, ':')"/>
        <!-- Eg. provvedimento:estremi[:annesso..][@versione][*comunicato..][$manifestazione][#id] -->
        <xsl:variable name="provvedimento" select="substring-before($i2, ':')"/>
        <!-- Eg. provvedimento -->
        <xsl:variable name="i3" select="substring-after($i2, ':')"/>
        <!-- Eg. estremi[:annesso..][@versione][*comunicato..][$manifestazione][#id] -->
        <xsl:variable name="n1" select="substring-before($i3, ':')"/> 
        <xsl:variable name="n2" select="substring-before($i3, '@')"/>
        <xsl:variable name="n3" select="substring-before($i3, '*')"/>
        <xsl:variable name="n4" select="substring-before($i3, '#')"/>
        <xsl:variable name="estremi">
            <xsl:choose>
                <xsl:when test='$n1'><xsl:value-of select="$n1"/></xsl:when>
                <xsl:when test='$n2'><xsl:value-of select="$n2"/></xsl:when>
                <xsl:when test='$n3'><xsl:value-of select="$n3"/></xsl:when>
                <xsl:when test='$n4'><xsl:value-of select="$n4"/></xsl:when>
                <xsl:otherwise><xsl:value-of select="$i3"/></xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <!-- Eg. 2010-03-08;nir-s2102504 -->
        <xsl:variable name="data" select="substring-before($estremi, ';')"/>
        <xsl:variable name="num" select="substring-after($estremi, ';')"/>
        
        <xsl:variable name="id" select="substring-after($urn, '#')"/>

        <!-- Output -->
        <xsl:if test="starts-with($urn, 'urn:nir')">
            <xsl:text>/akn/it/</xsl:text>
            <xsl:choose>
                <xsl:when test="$provvedimento = 'decreto.legislativo'"><xsl:text>act</xsl:text></xsl:when>
                <xsl:when test="$provvedimento = 'decreto'"><xsl:text>act</xsl:text></xsl:when>
                <xsl:otherwise><xsl:text>act</xsl:text></xsl:otherwise>
            </xsl:choose>
            <xsl:text>/</xsl:text>
            <xsl:value-of select="$provvedimento"/>
            <xsl:text>/</xsl:text>
            <xsl:value-of select="$autorita"/>
            <xsl:text>/</xsl:text>
            <xsl:value-of select="$data"/>
            <xsl:text>/</xsl:text>
            <xsl:value-of select="$num"/>
            
            <!-- Questo serve solo in caso di manifestation 
                <xsl:value-of select="'/ita'"/> -->
        </xsl:if>
        <xsl:if test="$id">
            <!-- Se siamo in fondo ad un uri dobbiamo mettere la manifestation -->
            <xsl:if test="starts-with($urn, 'urn:nir')">
                <xsl:text>/ita/</xsl:text>
                <xsl:value-of select="$data"/>
            </xsl:if>
            <xsl:text>#</xsl:text>
            <xsl:if test="//node()[@id = $id]">
                <xsl:apply-templates mode="genera_id" select="//node()[@id = $id]"/>
            </xsl:if>
            <xsl:if test="not(//node()[@id = $id])">
                <xsl:value-of select="$id"/>
            </xsl:if>
        </xsl:if>
    </xsl:template>

    <xsl:template match="node()|@*" mode="copyEverything">
        <xsl:copy>
            <xsl:apply-templates select="node()|@*" mode="copyEverything"/>
        </xsl:copy>
    </xsl:template> 
</xsl:stylesheet>