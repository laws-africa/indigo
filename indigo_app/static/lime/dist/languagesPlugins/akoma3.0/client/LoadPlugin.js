/*
 * Copyright (c) 2014 - Copyright holders CIRSFID and Department of
 * Computer Science and Engineering of the University of Bologna
 * 
 * Authors: 
 * Monica Palmirani – CIRSFID of the University of Bologna
 * Fabio Vitali – Department of Computer Science and Engineering of the University of Bologna
 * Luca Cervone – CIRSFID of the University of Bologna
 * 
 * Permission is hereby granted to any person obtaining a copy of this
 * software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 * 
 * The Software can be used by anyone for purposes without commercial gain,
 * including scientific, individual, and charity purposes. If it is used
 * for purposes having commercial gains, an agreement with the copyright
 * holders is required. The above copyright notice and this permission
 * notice shall be included in all copies or substantial portions of the
 * Software.
 * 
 * Except as contained in this notice, the name(s) of the above copyright
 * holders and authors shall not be used in advertising or otherwise to
 * promote the sale, use or other dealings in this Software without prior
 * written authorization.
 * 
 * The end-user documentation included with the redistribution, if any,
 * must include the following acknowledgment: "This product includes
 * software developed by University of Bologna (CIRSFID and Department of
 * Computer Science and Engineering) and its authors (Monica Palmirani, 
 * Fabio Vitali, Luca Cervone)", in the same place and form as other
 * third-party acknowledgments. Alternatively, this acknowledgment may
 * appear in the software itself, in the same form and location as other
 * such third-party acknowledgments.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 * OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 * IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
 * CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
 * TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

/**
 * This is the plugin for loading documents
 */

Ext.define('LIME.ux.LoadPlugin', {
    singleton : true,
    alternateClassName : 'LoadPlugin',
    
    config: {
        authorialNoteClass: 'authorialNote',
        metadataClass: 'meta',
        refToAttribute: 'noteref',
        noteTmpId: 'notetmpid',
        tmpSpanCls: 'posTmpSpan'
    },

    beforeLoad : function(params) {
        var metaResults = [], documents, treeData = [];
        if (params.docDom) {
            documents = params.docDom.querySelectorAll('*[class~=' + DocProperties.documentBaseClass + ']');
            if(documents.length) {
                Ext.each(documents, function(doc, index) {
                    metaResults.push(Ext.Object.merge(this.processMeta(doc, params), {docDom: doc}));
                }, this);    
            } else {
                metaResults.push(this.processMeta(null, params));
            }
            
            this.preProcessNotes(params.docDom);
                   
            // Set the properties of main document which is the first docuemnt found
            // params object contains properties inserted by user, 
            // metaResults contains properties founded in the document
            metaResults[0].docLang = metaResults[0].docLang || params.docLang;
            metaResults[0].docLocale = metaResults[0].docLocale || params.docLocale;
            metaResults[0].docType = metaResults[0].docType || params.docType;
            params.docLang = metaResults[0].docLang;
            params.docLocale = metaResults[0].docLocale;
            params.docType = metaResults[0].docType;
            params.metaDom = metaResults[0].metaDom;
        } else {
            metaResults.push(this.processMeta(null, params));
            metaResults[0].docType = params.docType;
            params.metaDom = metaResults[0].metaDom;
        }
        params.treeData = treeData;
        params.metaResults = metaResults;
        return params;
    },

    afterLoad : function(params, app) {
        var me = this, 
            schemaUrl = Config.getLanguageSchemaPath(),
            docCls = DocProperties.getDocClassList(),
            langId = Language.getAttributePrefix()+Language.getElementIdAttribute();
        Ext.Ajax.request({
            url : schemaUrl,
            method : 'GET',
            scope : this,
            success : function(result, request) {
                var doc = DomUtils.parseFromString(result.responseText);
                if(doc) {
                    me.langSchema = doc;
                    me.getMetaDataStructure(doc);
                }
            }
        });
        documentNode = params.docDom.querySelector('*[class="'+docCls+'"]');
        if(documentNode && !documentNode.getAttribute("akn_name")) {
            documentNode.setAttribute("akn_name", DocProperties.getDocType());
        }

        Ext.each(params.docDom.querySelectorAll('['+Language.attributePrefix+'class'+']'), function(node) {
            var align = node.getAttribute(Language.attributePrefix+'class');
            if ( !Ext.isEmpty(align) ) {
                node.setAttribute('style', 'text-align: '+align+';');
            }
        });

        // Add proprietary namespace for the given locale if it is missing
        if(DocProperties.documentInfo.docLocale == 'uy') {
            var el = params.docDom.querySelector('.document');
            if (el && !el.getAttribute("xmlns:uy"))
                el.setAttribute("xmlns:uy", "http://uruguay/propetary.xsd");
        }

        // Remove all note ref numbers from Word imported documents.
        Ext.each(params.docDom.querySelectorAll('span.noteRefNumber'), function(node) {
            node.parentNode.removeChild(node);
        });

        me.insertFrbrData(params);
    },

    insertFrbrData: function(params) {
        var me = this,
            nodes, date = Ext.Date.format(new Date(), 'Y-m-d'),
            tmpNode, author = "#limeEditor", workUri, workUriTpl,
            expUri, expUriTpl, manUri, manUriTpl;

        if(params.metaDom) {
           workUriTpl = new Ext.Template('/{docLocale}/{docType}/{date}/{number}');
           workUri = workUriTpl.apply(Ext.merge(params, {
                date: date,
                number: ""
           }));
           expUriTpl = new Ext.Template('{workUri}/{lang}@');
           expUri = expUriTpl.apply({
                workUri: workUri,
                lang: params.docLang
           });
           manUriTpl = new Ext.Template('{expUri}/main.xml');
           manUri = manUriTpl.apply({
                expUri: expUri
           });

           tmpNode = params.metaDom.querySelector("*[class=FRBRWork] *[class=FRBRuri]");
           me.setMetaAttribute(tmpNode, "value", workUri);
           tmpNode = params.metaDom.querySelector("*[class=FRBRWork] *[class=FRBRthis]");
           me.setMetaAttribute(tmpNode, "value", workUri);

           tmpNode = params.metaDom.querySelector("*[class=FRBRExpression] *[class=FRBRuri]");
           me.setMetaAttribute(tmpNode, "value", expUri);
           tmpNode = params.metaDom.querySelector("*[class=FRBRExpression] *[class=FRBRthis]");
           me.setMetaAttribute(tmpNode, "value", expUri);

           tmpNode = params.metaDom.querySelector("*[class=FRBRManifestation] *[class=FRBRuri]");
           me.setMetaAttribute(tmpNode, "value", manUri);
           tmpNode = params.metaDom.querySelector("*[class=FRBRManifestation] *[class=FRBRthis]");
           me.setMetaAttribute(tmpNode, "value", manUri);

           nodes = params.metaDom.querySelectorAll("*[class=FRBRdate]");
           Ext.each(nodes, function(node) {
                me.setMetaAttribute(node, "date", date);
           });

           tmpNode = params.metaDom.querySelector("*[class=FRBRWork] *[class=FRBRauthor]");
           me.setMetaAttribute(tmpNode, "akn_href", '#author');
           me.setMetaAttribute(tmpNode, "as", '#author');
           nodes = params.metaDom.querySelectorAll("*[class=FRBRauthor]");
           Ext.each(nodes, function(node) {
                me.setMetaAttribute(node, "akn_href", author);
                me.setMetaAttribute(node, "as", author);
           });

           tmpNode = params.metaDom.querySelector("*[class=FRBRWork] *[class=FRBRcountry]");
           me.setMetaAttribute(tmpNode, "value", params.docLocale);
           tmpNode = params.metaDom.querySelector("*[class=FRBRExpression] *[class=FRBRlanguage]");
           me.setMetaAttribute(tmpNode, "language", params.docLang);

           tmpNode = params.metaDom.querySelector("*[class=publication]");
           me.setMetaAttribute(tmpNode, "date", date);

           tmpNode = params.metaDom.querySelector("*[class=references]");

           var person = {
                name: "TLCPerson",
                attributes: [{
                    name: "eId",
                    value: "limeEditor"
                },{
                    name: "akn_href",
                    value: "/lime.cirsfid.unibo.it"
                },{
                    name: "showAs",
                    value: "LIME editor"
                }]
            };
            
            if(tmpNode) {
                personNode = me.objToDom(params.metaDom.ownerDocument, person);
                if ( !tmpNode.querySelector('[eId=limeEditor]') ) {
                    tmpNode.appendChild(personNode);
                }
            }
        }
    },

    objToDom: function(doc, obj) {
        var me = this, node, childNode;
        if(obj.name) {
            node = doc.createElement("div");
            node.setAttribute("class", obj.name);
            Ext.each(obj.attributes, function(attribute) {
                node.setAttribute(attribute.name, attribute.value);
            });
            if(!Ext.isEmpty(obj.text)) {
                childNode = doc.createTextNode(obj.text);
                node.appendChild(childNode);               
            } else {
                Ext.each(obj.children, function(child) {
                    childNode = me.objToDom(doc, child);
                    if(childNode) {
                        node.appendChild(childNode);
                    }
                });    
            }
        }
        return node;
    },

    setMetaAttribute: function(node, name, value) {
        if(node && Ext.isEmpty(node.getAttribute(name))) {
            node.setAttribute(name, value);
        }
    },
    
    getMetaDataStructure: function(schemaDoc) {
        var me = this;
        var elements = me.getSchemaElements(schemaDoc, "meta");
        if(elements) {
            Language.setMetadataStructure(elements);
        }
    },
    
    getSchemaElements: function(schema, elementName) {
        var me = this, 
            element = schema.querySelector("element[name = '"+elementName+"']"),
            children = [],
            obj = {};
        if(element) {
            obj.name = elementName;
            Ext.each(element.querySelectorAll("element"), function(child) {
                var name = child.getAttribute("ref"),
                    chObj = me.getSchemaElements(schema, name);
                if(chObj) {
                    children.push(chObj);
                }
            });
            obj.children = children;    
        } else {
            return null;
        }
        return obj;
    },
    
    processMeta: function(doc, params) {
        var extdom, meta, result = {}, ownDoc;
        
        result.docMarkingLanguage = params.docMarkingLanguage;
        
        if(!doc || !doc.querySelector("*[class="+this.getMetadataClass()+"]")) {
            result.metaDom = this.createBlankMeta();
        }  else {
            extdom = new Ext.Element(doc);
            meta = extdom.down("*[class=" + this.getMetadataClass() + "]");
            result = {}, ownDoc = doc.ownerDocument;
            result.docType = DomUtils.getDocTypeByNode(doc);
            if (meta && meta.dom.parentNode) {
                var language = meta.down("*[class=FRBRlanguage]", true),
                    country = meta.down("*[class=FRBRcountry]", true);
    
                if (language) {
                    result.docLang = language.getAttribute('language');
                }
                if (country) {
                    result.docLocale = country.getAttribute('value');
                }
                result.metaDom = meta.dom.parentNode.removeChild(meta.dom);
            }
        }         
        
        return result;
    },
    
    createBlankMeta: function() {
        var meta = Utilities.jsonToHtml(Config.getLanguageConfig().metaTemplate);
        if(meta) {
            meta.setAttribute('class', this.getMetadataClass());
            return meta;
        }
    },
    
    /*
     * Is important to call this function before loading the document in the editor. 
     * */
    preProcessNotes : function(dom) {
        var athNotes = dom.querySelectorAll("*[class~=" + this.getAuthorialNoteClass() + "]"),
            markerTemplate = new Ext.Template('<span class="'+this.getTmpSpanCls()+'" '+this.getRefToAttribute()+'="{ref}"></span>');
            
        Ext.each(athNotes, function(element, index) {
            var noteTmpId = "note_"+index;
            Ext.DomHelper.insertHtml("beforeBegin", element, markerTemplate.apply({
                'ref' : noteTmpId
            }));
            element.setAttribute(this.getNoteTmpId(), noteTmpId);
            // Move the element to the end of parent to prevent split in parent
            if(element.nextSibling) {
                element.parentNode.appendChild(element);
            }
        }, this);
    }
});