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

Ext.define('LIME.controller.DocumentCollectionController', {
    extend : 'Ext.app.Controller',

    views : ['LIME.ux.documentCollection.NewDocumentCollection'],

    refs : [{
        selector : 'appViewport',
        ref : 'appViewport'
    },{
        selector: '*[cls=docCollectionTab]',
        ref: 'docCollectionTab'
    },{
        selector: 'markingMenu',
        ref: 'markingMenu'
    }],
    
    config: {
        pluginName: "documentCollection",
        colModSuffix: "-mod",
        docColAlternateType: "documentCollectionContent"
    },

    originalBeforeTranslate: false,
    
    onDocumentLoaded : function(docConfig) {
        var me = this, app = me.application, docsType = Config.getDocTypesName(), 
            menu, beforeTranslate = TranslatePlugin.beforeTranslate,
            collTab = me.getDocCollectionTab(), tabPanel = collTab.up();

        // Create snapshot and documents tree only if the load is not light load but a complete one
        if (!docConfig.lightLoad) {
            if (Ext.Array.indexOf(docsType, "documentCollection") != -1) {
                menu = {
                    text : Locale.getString("newCollectionText", me.getPluginName()),
                    icon : 'resources/images/icons/package_add.png',
                    name : 'newDocCollection',
                    handler : Ext.bind(this.newDocumentCollection, this, [false])
                };
                app.fireEvent("addMenuItem", me, {
                    menu: "fileMenuButton",
                    after: "newDocumentButton"
                }, menu);
            }
            me.completeEditorSnapshot = me.createEditorSnapshot();
            me.setDocumentTreeData(docConfig);
            // Disables the document collection tab if the opened document is not a document collection
            if (docConfig.docType != "documentCollection") {
                tabPanel.setActiveTab(0);
                tabPanel.getTabBar().items.items[1].disable();
            } else {
                // Wrap beforeTrasnalte for customizate it
                TranslatePlugin.beforeTranslate = function(params) {
                    me.originalBeforeTranslate = me.originalBeforeTranslate || 
                                                Ext.Function.bind(beforeTranslate, TranslatePlugin);
                    var newParams = me.originalBeforeTranslate(params) || params;
                    return me.docCollectionBeforeTranslate(newParams);
                };
            }
        }
        
        if (docConfig.docType == "documentCollection" && !docConfig.colectionMod) { 
            tabPanel.setActiveTab(collTab);
            tabPanel.getTabBar().items.items[0].disable();
            tabPanel.getTabBar().items.items[1].enable();
            app.fireEvent(Statics.eventsNames.disableEditing);
        } else {
            tabPanel.setActiveTab(0);
            tabPanel.getTabBar().items.items[0].enable();
            app.fireEvent(Statics.eventsNames.enableEditing);
        }
       
        me.selectActiveDocument(docConfig.treeDocId, true);
    },
    
    newDocumentCollection : function(modify) {
        var newWindow = Ext.widget('newDocumentCollection'),
            grid = newWindow.down("*[cls=dropArea] grid");
        if (modify) {
            newWindow.setData(DocProperties.documentInfo);
            newWindow.isModify = true;
        } else {
            grid.getStore().removeAll();
        }
        newWindow.onAddColumn = Ext.bind(this.onAddColumn, this);
        newWindow.show();
    },
    
    docCollectionBeforeTranslate: function(params) {
        var me = this, dom = params.docDom, metaConf = DocProperties.docsMeta, 
            documents, snapshot, tmpDom, rootEl;
            
        // Checking if the request is before saving the document
        if (params.complete && me.completeEditorSnapshot) {
            snapshot = me.updateEditorSnapshot(me.completeEditorSnapshot);
            if(snapshot.dom) {
                tmpDom = DomUtils.parseFromString(snapshot.content);
                DomUtils.moveChildrenNodes(tmpDom, dom);
            }
        }
        documents = dom.querySelectorAll("*["+DocProperties.docIdAttribute+"]");
        // Insert the metadata which was removed before loading
        if (metaConf) {
            Ext.each(documents, function(doc, index) {
                var docId = doc.getAttribute(DocProperties.docIdAttribute),
                    metaDom;
                /* The first document is processed by the editor 
                 * here we process the documents inside the first document 
                 * e.g. documentCollection */
                docId = (docId!=undefined) ? parseInt(docId) : undefined;
                if (docId != 0 && metaConf[docId] && metaConf[docId].metaDom) {
                    metaDom = Ext.clone(metaConf[docId].metaDom);
                    metaDom.setAttribute("class", "meta");
                    if ( doc.firstChild && !Ext.fly(doc.firstChild).is('.meta') ) {
                        doc.insertBefore(metaDom, doc.firstChild);    
                    }
                }
            }, this);       
        }
        if (me.completeEditorSnapshot && me.completeEditorSnapshot.dom) {
            rootEl = me.completeEditorSnapshot.dom.querySelector("*["+DocProperties.markingLanguageAttribute+"]");
            tmpDom = dom.querySelector("*["+DocProperties.markingLanguageAttribute+"]");    
            if(!tmpDom && rootEl) {
                Ext.each(rootEl.attributes, function(el) {
                    dom.setAttribute(el.nodeName, el.nodeValue);
                });
            }
        }

        params.docDom = dom;
        return params;
    },
    
    createEditorSnapshot: function(config) {
        var editor = this.getController('Editor'),
            newSnapshot = {
                content: editor.getContent()
            };
        newSnapshot.dom = DomUtils.parseFromString(newSnapshot.content);
        return newSnapshot;
    },
    
    updateEditorSnapshot: function(snapshot) {
        var me = this, editor = me.getController('Editor'),
            newSnapshot = me.createEditorSnapshot(),
            snapshotDoc, newSnapshot, editorDoc, editorDocId;
        if (newSnapshot.dom) {
            editorDoc = newSnapshot.dom.querySelector("*["+DocProperties.docIdAttribute+"]");
            if (editorDoc) {
                editorDocId = editorDoc.getAttribute(DocProperties.docIdAttribute);
                if(me.isDocColMod(editorDoc)) {
                    snapshot.dom = me.docColModToSnapshot(editorDoc, editorDocId, snapshot);
                } else if (parseInt(editorDocId) === 0) {
                    snapshot.dom = newSnapshot.dom;
                } else {
                    Utilities.replaceChildByQuery(snapshot.dom, "["+DocProperties.docIdAttribute+"='" + editorDocId + "']", editorDoc);
                }
                snapshot.content = DomUtils.serializeToString(snapshot.dom);
            }
        }
        return Ext.merge(snapshot, {editorDocId: editorDocId});
    },
    
    isDocColMod: function(doc) {
        var colMod = parseInt(doc.getAttribute("colmod"));
        if(isNaN(colMod)) {
            return false;
        }
        return (colMod) ? true : false;
    },
    
    docToTreeData: function(doc, dom, textSufix, qtip) {
        var res = {}, collBody, children, docChildren = [],
            languageController = this.getController("Language"),
            langPrefix = languageController.getLanguagePrefix(), chDoc, cmpDoc;
        if (doc) {
            if(Ext.DomQuery.is(doc, "[class~=documentCollection]")) {
                docChildren.push({text: doc.getAttribute(langPrefix+"name") || "collection",
                   leaf: true, 
                   id: doc.getAttribute("docid")+this.getColModSuffix(),
                   qtip: "collection"});
            }
            collBody = doc.querySelector("*[class*=collectionBody]");
            children = (collBody) ? DomUtils.filterMarkedNodes(collBody.childNodes) : [];
            for (var i = 0; i < children.length; i++) {
                cmpDoc = children[i];
                if (cmpDoc.getAttribute("class").indexOf("component") != -1) {
                    cmpDoc = DomUtils.filterMarkedNodes(cmpDoc.childNodes)[0];
                }
                if(cmpDoc) {
                    if (DomUtils.getElementNameByNode(cmpDoc) == "documentRef") {
                        var docRef = cmpDoc.getAttribute(langPrefix+"href");
                        docRef = (docRef) ? docRef.substr(1) : ""; //Removing the '#'
                        if (docRef) {
                            chDoc = dom.querySelector("*[class~='components'] *["+langPrefix+Language.getElementIdAttribute()+"="+docRef+"] *[class*="+DocProperties.documentBaseClass+"]") 
                                    || dom.querySelector("*[class~='components'] *["+langPrefix+Language.getElementIdAttribute().toLowerCase()+"="+docRef+"] *[class*="+DocProperties.documentBaseClass+"]");
                            if (chDoc) {
                                docChildren.push(this.docToTreeData(chDoc, dom, '#'+docRef, cmpDoc.getAttribute(langPrefix+"showAs")));    
                            }
                        }
                    } else if(cmpDoc.getAttribute("class").indexOf(DocProperties.documentBaseClass) != -1) {
                        docChildren.push(this.docToTreeData(cmpDoc, dom));
                    }
                }
                
            }
            res = {text:DomUtils.getDocTypeByNode(doc) + ((textSufix) ? " "+ textSufix : ""),
                   children: docChildren, 
                   leaf: (docChildren.length == 0), 
                   expanded : (docChildren.length != 0),
                   id: parseInt(doc.getAttribute("docid")),
                   qtip: qtip};
        }
        return res;
    },
    
    selectActiveDocument: function(docId, persistent) {
        var openedDocumentsStore = this.getStore('OpenedDocuments'),
            treePanel = this.getDocCollectionTab().down("treepanel"),
            node;
        
        docId = (docId == -1) ? this.selectedDocId : docId;
        node = (docId) ? openedDocumentsStore.getNodeById(docId) : openedDocumentsStore.getRootNode().firstChild;

        if (node) {
            treePanel.getSelectionModel().select(node, false, true);    
        }
        if (persistent) {
            this.selectedDocId = docId;
        }
    },
    
    setDocumentTreeData: function(docConfig) {
        var openedDocumentsStore = this.getStore('OpenedDocuments'), treeData = [];  
        if (docConfig.docDom && docConfig.docType == "documentCollection") {
            var currentDocument = docConfig.docDom.querySelector("*[class*="+docConfig.docType+"]"); 
            treeData.push(this.docToTreeData(currentDocument, docConfig.docDom));
        }
        openedDocumentsStore.setRootNode({children: treeData});
    },

    onAddColumn : function(columnDescriptor) {
        var config = {};
        if (columnDescriptor && (columnDescriptor.fieldName == "version" || columnDescriptor.fieldName == "docName")) {
            config = {
                viewConfig : {
                    plugins : {
                        ptype : 'gridviewdragdrop',
                        dragGroup : 'secondGridDDGroup',
                        dropGroup : 'firstGridDDGroup',
                        dragText : Locale.getString("dragDocText", this.getPluginName())
                    }
                },
                cls : 'draggableGrid'
            };
        }
        return config;
    },
    
    createDocumentCollection: function(config, componentsUri) {
        var serializedUri = "";
        if (componentsUri.length > 0) {
            // serialize the array to pass to the service
            serializedUri = componentsUri.join(";");
            this.makeDocumentCollectionRequest(config, {docs: serializedUri});
        }
    },
    
    makeDocumentCollectionRequest: function(config, params) {
        var loginManager = this.getController('LoginManager'),
            userInfo = loginManager.getUserInfo(), app = this.application,
            newParams = Ext.merge({
                requestedService : Statics.services.createDocumentCollection,
                docCollectionName : "",
                userName : userInfo.username,
                userPassword : userInfo.password,
                docLang: config.docLang,
                docLocale: config.docLocale,
                markingLanguage: config.docMarkingLanguage
            }, params);

        Ext.Ajax.request({
            // the url of the web service
            url : Utilities.getAjaxUrl(),
            method : 'POST',
            // send the content in XML format
            params : newParams,
            scope : this,
            success : function(result, request) {
                app.fireEvent(Statics.eventsNames.loadDocument, Ext.Object.merge(config, {
                    docText : result.responseText
                }));
                
                if (Ext.isFunction(config.success)) {
                    config.success();
                }
            },
            failure: function() {
                if (Ext.isFunction(config.failure)) {
                    config.failure();
                }
            }
        });
    },
    
    modifyDocumentCollection: function(config, components, classes) {
        var me = this, serializedUri = "", serializedCls = "",
            params = {};
        if (components.length > 0) {
            // serialize the array to pass to the service
            serializedUri = components.join(";");
            serializedCls = classes.join(";");
            params = {
                modify: true,
                docs: serializedUri, 
                cls: serializedCls
            };
            // Saving mode to translate content from the snapshot
            me.application.fireEvent(Statics.eventsNames.translateRequest, function(xml) {
                me.makeDocumentCollectionRequest(config, Ext.Object.merge(params, {source: xml}));
            }, {complete: true});
        }
    },
    
    switchDoc: function(config) {
        var me = this, app = me.application, editor = me.getController('Editor'),
            docId = Ext.isString(config.id) ? parseInt(config.id) : config.id,
            docMeta = DocProperties.docsMeta[docId],
            colMod = Ext.isString(config.id) ? (config.id.indexOf(me.getColModSuffix()) != -1) : false;
            snapshot = me.completeEditorSnapshot, prevColMod = 0;

        if (snapshot && snapshot.dom) {
            /* Before loading a new document we need to update 
             * the snapshot with new content from the editor
             */
            newSnapshot = me.updateEditorSnapshot(snapshot);
            // Select the document in the snapshot and load it
            doc = (docId === 0) ? snapshot.dom : snapshot.dom.querySelector("*["+DocProperties.docIdAttribute+"='" + docId + "']");
            prevColMod = doc.querySelector("[colmod]");
            prevColMod = (prevColMod) ? parseInt(prevColMod.getAttribute("colmod")) : 0;
            if (doc && ((docId != parseInt(newSnapshot.editorDocId)) || colMod || prevColMod)) {
                if(colMod) {
                    doc = me.snapshotToDocColMod(snapshot, docId);
                    docTypeAlternateName = "";
                }
                var docEl = doc.querySelector("["+DocProperties.docIdAttribute+"]");
                if(docEl) {
                    docEl.setAttribute("colmod", (colMod) ? 1 : 0);
                }
                app.fireEvent(Statics.eventsNames.loadDocument, Ext.Object.merge(docMeta, {
                    docMarkingLanguage: Config.getLanguage(),
                    docText : DomUtils.serializeToString(doc),
                    alternateDocType: (colMod) ? me.getDocColAlternateType() : null,
                    lightLoad : true,
                    treeDocId : config.id,
                    colectionMod : colMod
                })); 
            }
        }
    },
    
    snapshotToDocColMod: function(snapshot, docId) {
        // Create a temporary copy of the snapshot, don't modify it directly!
        var breakingElement, completeSnapshotDom = DomUtils.parseFromString(snapshot.content),
            doc = (docId === 0) ? completeSnapshotDom : completeSnapshotDom.querySelector("*["+DocProperties.docIdAttribute+"='" + docId + "']"),
            docCol = completeSnapshotDom.querySelector("*["+DocProperties.docIdAttribute+"='" + docId + "']"),
            colBody;
        Utilities.removeNodeByQuery(doc, "[class*=components]");
        if(docCol) {
            colBody = docCol.querySelector("[class*=collectionBody]");
            //Utilities.removeNodeByQuery(docCol, "[class*=collectionBody]");
            if(colBody) {
                // Add breaking element to be able to insert text
                Ext.DomHelper.insertHtml('beforeBegin', colBody, "<span class=\""+DomUtils.breakingElementClass+"\"></span>");    
            }
        }
        return doc;
    },
    
    docColModToSnapshot: function(doc, docId, snapshot) {
        var completeSnapshotDom = DomUtils.parseFromString(snapshot.content), oldDoc, collectionBody;
        if (completeSnapshotDom) {
            /*oldDoc = completeSnapshotDom.querySelector("["+DocProperties.docIdAttribute+"='" + docId + "']");
            if (oldDoc) {
                collectionBody = oldDoc.querySelector("[class*=collectionBody]");
                doc.appendChild(collectionBody);    
            }*/
            Utilities.replaceChildByQuery(completeSnapshotDom, "["+DocProperties.docIdAttribute+"='" + docId + "']", doc);    
        }
        return completeSnapshotDom;
    },
    
    getDocumentsFromSnapshot: function(snapshot) {
        var domDocs, documents = [], metaConf = DocProperties.docsMeta;
        if (snapshot && snapshot.dom) {
            domDocs = snapshot.dom.querySelectorAll("*["+DocProperties.docIdAttribute+"]");
            Ext.each(domDocs, function(doc, index) {
                var docId = doc.getAttribute(DocProperties.docIdAttribute),
                    metaDom, uri;
                docId = (docId!=undefined) ? parseInt(docId) : undefined;
                // Document with id '0' is the collection 
                if (docId != 0 && metaConf[docId] && metaConf[docId].metaDom) {
                    metaDom = metaConf[docId].metaDom;
                    uri = metaDom.querySelector("*[class=FRBRManifestation]>*[class=FRBRthis]");
                    uri = (uri) ? uri : metaDom.querySelector("*[class=FRBRExpression]>*[class=FRBRuri]");
                    uri = uri.getAttribute("value");
                    documents.push({
                        id: uri,
                        cls: 'xml',
                        path: uri
                    });
                }
            }, this);
        }
        return documents;
    },
    
    onRemoveController: function() {
        var me = this;
        me.application.removeListener(Statics.eventsNames.afterLoad, me.onDocumentLoaded, me);
    },
    
    onInitPlugin: function() {
        var me = this;
        me.application.on(Statics.eventsNames.afterLoad, me.onDocumentLoaded, me);
    },
    
    init: function() {
        var me = this;
        me.control({
            '*[cls=modifyDocColl]': {
                click: function() {
                    me.newDocumentCollection(true);
                }
            },
            '*[cls=docCollectionTab] treepanel': {
                itemclick : function(view, rec, item, index, eventObj) {
                    me.switchDoc(rec.getData());
                },
                afterrender: function() {
                    me.selectActiveDocument(-1);
                }     
            },
            'newDocumentCollection': {
                afterrender: function(cmp) {
                    var collectionGrid = cmp.down("*[cls=dropArea] grid"), 
                    config, gridStore, components = [];
                    if (!cmp.isModify) return;
                    components = this.getDocumentsFromSnapshot(me.completeEditorSnapshot);
                    if (collectionGrid) {
                        gridStore = collectionGrid.getStore();
                        gridStore.loadData(components);
                    }
                }
            },
            'newDocumentCollection button[cls=createDocumentCollection]' : {
                click : function(cmp) {
                    var relatedWindow = cmp.up('window'), collectionGrid = relatedWindow.down("*[cls=dropArea] grid"), config, 
                        gridStore, components = [], languageController = this.getController("Language"),
                        classes = [];
                    if (collectionGrid) {
                        gridStore = collectionGrid.getStore();
                        gridStore.each(function(record) {
                            components.push(record.get('id'));
                            classes.push(record.get('cls'));
                        });
                    }
                    config = {
                        success : function() {
                            relatedWindow.close();
                        },
                        failure : function() {
                            Ext.Msg.alert('Error', 'Error');
                        }
                    };
                    if(relatedWindow.isModify) {
                        me.modifyDocumentCollection(Ext.Object.merge(config, relatedWindow.getData()), components, classes);
                    } else {
                        me.createDocumentCollection(Ext.Object.merge(config, relatedWindow.getData()), components);    
                    }
                }
            },
            'newDocumentCollection *[cls=dropArea] gridview' : {
                drop : function(node, data, dropRec, dropPosition) {
                    var record = data.records[0], store = record.store;
                    if (record.get('cls') == "folder") {
                        store.requestNode = record.get('id');
                        store.load({
                            addRecords : true,
                            scope : this,
                            callback : function(records, operation, success) {
                                var oldRecordIndex = store.indexOf(record);
                                // Remove the "version" record
                                store.remove(record);
                                // If new records are in the wrong position move they
                                if (store.indexOf(records[0]) != oldRecordIndex) {
                                    store.remove(records);
                                    store.insert(oldRecordIndex, records);
                                }
                            }
                        });
                    }
                },
                beforedrop : function(node, data, overModel, dropPosition, dropHandlers) {
                    var record = data.records[0], relatedWindow = data.view.up("window"), dropGrid = relatedWindow.down("*[cls=dropArea] gridview");

                    dropHandlers.wait = true;
                    // Check if the record already exist in the store and cancel drop event if so
                    if (dropGrid != data.view && dropGrid.getStore().find('id', record.get('id')) != -1) {
                        dropHandlers.cancelDrop();
                    } else {
                        dropHandlers.processDrop();
                    }
                }
            }
        });
    }
});
