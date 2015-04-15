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

Ext.define('LIME.controller.ConsolidationController', {
    extend: 'Ext.app.Controller',
    
    views: ["LIME.ux.consolidation.ConsolidationMainTab"],

    refs: [{
        ref: 'consolidationPanel',
        selector: 'consolidationMainTab'
    }, {
        ref: 'modifiedDocField',
        selector: 'consolidationMainTab fieldset[cls=selectModified] textfield'
    }, {
        ref: 'modifyingDocField',
        selector: 'consolidationMainTab fieldset[cls=selectModifying] textfield'
    }, {
        ref: 'editButton',
        selector: '*[cls=editButton]'
    },{
        ref: 'mainEditor',
        selector: '#mainEditor mainEditor'
    }, {
        ref: 'secondEditor',
        selector: '#secondEditor mainEditor'
    }, {
        ref: 'appViewport',
        selector: 'appViewport'
    }, {
        ref: 'main',
        selector: 'main'
    }, {
        ref: 'explorer',
        selector: 'explorer'
    }, {
        ref: 'mainToolbar',
        selector: 'mainToolbar'
    }, {
        ref : 'markingMenuContainer',
        selector : '[cls=markingMenuContainer]'
    }],

    config: {
        pluginName: "consolidation",
    },
    
    // The document being modified.
    modifiedDoc: null,
    // The document containing the active 
    // modifications.
    modifyingDoc: null,

    init: function () {
        var me = this;
        
        me.application.on(Statics.eventsNames.afterLoad, me.afterDocumentLoaded, me);

        this.control({
            'consolidationMainTab fieldset[cls=selectModified] button': {
                click: function(cmp) {
                    me.showOpenDocumentDialog(function(doc) {
                        me.modifiedDoc = Ext.clone(doc);
                        me.updateFields();
                    });
                }
            },
            'consolidationMainTab fieldset[cls=selectModifying] button': {
                click: function(cmp) {
                    me.showOpenDocumentDialog(function(doc) {
                        me.modifyingDoc = Ext.clone(doc);
                        me.updateFields();
                    });
                }
            },
            'consolidationMainTab button[cls=resetButton]': {
                click: function(cmp) {
                    delete me.modifiedDoc;
                    delete me.modifyingDoc;
                    me.updateFields();
                }
            },
            'consolidationMainTab button[cls=consolidationButton]': {
                click: function(cmp) {
                    me.startConsolidation();
                }
            }
        });
    },

    // Show the select document dialog and call
    // callback with the selected document.
    showOpenDocumentDialog: function (cb) {
        var me = this;
        var config = {
            callback: cb,
            scope: me
        };
        me.application.fireEvent(Statics.eventsNames.selectDocument, config); 
    },

    // Display the document path inside the selected document fields.
    updateFields: function () {
        var modifiedVal = this.modifiedDoc ? this.modifiedDoc.path : '';
        this.getModifiedDocField().setValue(modifiedVal);

        var modifyingVal = this.modifyingDoc ? this.modifyingDoc.path : '';
        this.getModifyingDocField().setValue(modifyingVal);
    },

    parseDocuments: function() {
        var me = this, modController = this.getController('ModificationController'),
            editorController = me.getController("Editor");

        if ( me.secondDocumentConfig && me.secondDocumentConfig.metaDom ) {
            var activeModifications = me.secondDocumentConfig.metaDom.querySelectorAll('*[class~=activeModifications] > *');
            if ( activeModifications.length ) {
                var modifyingDom = editorController.getDom(me.secondEditor);
                var modifiedDom = editorController.getDom();
                modController.consolidate(activeModifications, modifyingDom, modifiedDom);
            } else {
                Ext.Msg.alert('Warning', 'There are no active modifications');
            }
        }
    },

    // Switch to dual editing mode.
    startConsolidation: function () {
        var dualConfig = {
            "editableDoc": this.modifiedDoc.id,
            "notEditableDoc": this.modifyingDoc.id
        };
        // var dualConfig={editableDoc: 
        //     "/db/wawe_users_documents/aasd.gmail.com/my_documents/it/doc.xml", 
        //     notEditableDoc: 
        //     "/db/wawe_users_documents/aasd.gmail.com/my_documents/it/veto.xml"};
        console.log(dualConfig);

        var me = this,
            mainTabPanel = me.getMain(),
            explorer = me.getExplorer(),
            markingMenu = me.getMarkingMenuContainer(),
            editorTab = me.getMainEditor().up(),
            storage = me.getController("Storage"),
            editorController = me.getController("Editor"),
            language = me.getController("Language"),
            consolidationTab = mainTabPanel.down("consolidationMainTab"),
            secondEditor;

        //me.getAppViewport().setLoading(true);

        editorTab.noChangeModeEvent = true;

        // Set active the editor tab
        mainTabPanel.setActiveTab(editorTab);

        if(consolidationTab) {
            consolidationTab.tab.hide();  
        }

        var tinyView = editorController.getEditorComponent();
        var tinyEditor = tinyView.editor;

        /*Ext.each(tinyNode.querySelectorAll('div.mce-toolbar'), function( toolbar ) {
            Ext.fly(toolbar).parent('.mce-first').hide();
        });*/

        tinyEditor.execCommand("contentReadOnly", false, tinyEditor.getElement());

        var body = tinyEditor.getBody();
        Ext.fly(body).addCls('readOnly');

        editorController.defaultActions = {
            noExpandButtons: true
        };
        
        //explorer.setVisible(false);

        explorer.up().remove(explorer);

        //markingMenu.collapse();

        if(markingMenu) {
            markingMenu.hide();//up().remove(markingMenu);
        }
        
        secondEditor = me.createSecondEditor();
        me.secondEditor = secondEditor;
        var el2 = Ext.fly(editorController.getEditor(editorController.getSecondEditor()).getBody());
        el2.addCls('noboxes');
        el2.addCls('nocolors');
        el2.addCls('pdfstyle');

        editorController.getSecondEditor().up().setTitle(Locale.getString("modifyingDocument", "consolidation"));
        me.initialMainEditorTitle = editorController.getMainEditor().up().title;
        editorController.getMainEditor().up().setTitle(Locale.getString("modifiedDocument", "consolidation"));
        Ext.defer(function() {
          editorController.addContentStyle('#tinymce div.mod', 'padding-left: 15px', editorController.getSecondEditor());
          editorController.addContentStyle('#tinymce div.mod', 'border-radius: 0', editorController.getSecondEditor());
          editorController.addContentStyle('#tinymce div.mod', 'border-left: 5px solid #1B6427', editorController.getSecondEditor());
          
          editorController.addContentStyle('#tinymce div.quotedStructure', 'padding-left: 15px', editorController.getSecondEditor());
          editorController.addContentStyle('#tinymce div.quotedStructure', 'border-radius: 0', editorController.getSecondEditor());
          editorController.addContentStyle('#tinymce div.quotedStructure', 'border-left: 5px solid #ABB26E', editorController.getSecondEditor());
        }, 2000);

        me.addFinishEditingButton(secondEditor, consolidationTab);

        Ext.defer(function() {

            storage.openDocumentNoEditor(dualConfig.notEditableDoc, function(config) {
                language.beforeLoad(config, function(newConfig) {
                    me.secondDocumentConfig = newConfig;
                    editorController.loadDocument(newConfig.docText, newConfig.docId, secondEditor, true);
                    if(newConfig.metaDom) {
                        var manifestationUri = newConfig.metaDom.querySelector("*[class=FRBRManifestation] *[class=FRBRuri]");
                        if(manifestationUri) {
                            secondEditor.down("mainEditorUri").setUri(manifestationUri.getAttribute("value"));
                        }
                    }
                    me.manageAfterLoad = function() {
                        var newId = dualConfig.editableDoc.replace("/diff/", "/diff_modified/");
                        DocProperties.documentInfo.docId = newId;
                        me.parseDocuments();
                    };
                    storage.openDocument(dualConfig.editableDoc);
                }, true);
            });    
        }, 100);
    },

    stopConsolidation: function (editor, diff) {
        var me = this,
            mainTabPanel = me.getMain(),
            viewport = me.getAppViewport(),
            userInfo = this.getController('LoginManager').getUserInfo(),
            editorTab = me.getMainEditor().up(),
            newExplorer, language = me.getController("Language"),
            editorController = me.getController("Editor");

        if(me.finishEditBtn) {
            me.finishEditBtn.up().remove(me.finishEditBtn);
        }

        editorController.autoSaveContent(true);
        editorController.getMainEditor().up().setTitle(me.initialMainEditorTitle);
        Ext.fly(editorController.getBody()).addCls('readOnly');
        //this.getController('MarkingMenu').addMarkingMenu();
        me.getMarkingMenuContainer().show();
        this.getController('ModificationController').success();

        language.beforeTranslate(function(xml) {
            xml = xml.replace('<?xml version="1.0" encoding="UTF-8"?>', '');
            var params = {
                userName : userInfo.username,
                fileContent : xml,
                metadata: DomUtils.serializeToString(me.secondDocumentConfig.metaDom)
            };

            var url = me.secondDocumentConfig.docId.replace("/diff/", "/diff_modified/");

            me.application.fireEvent(Statics.eventsNames.saveDocument, url, params, function() {
                if(diff) {
                    diff.tab.show();
                    diff.enforceReload = true;
                    mainTabPanel.setActiveTab(diff);
                }

                editorTab.noChangeModeEvent = false;
                viewport.remove(editor);

                newExplorer = Ext.widget("explorer", {
                    region : 'west',
                    expandable : true,
                    resizable : true,
                    width : '15%',
                    autoScroll : true,
                    margin : 2
                });
                viewport.add(newExplorer);
            });
        }, {}, null, editor, me.secondDocumentConfig.metaDom);
    },

    createSecondEditor: function() {
        var secondEditor = Ext.widget("main", {
            id: 'secondEditor',
            resizable : true,
            region : 'west',
            width: '48%',
            margin : 2
        });

        this.getAppViewport().add(secondEditor);
        return secondEditor;
    },

    afterDocumentLoaded: function() {
        var me = this;
        if(Ext.isFunction(me.manageAfterLoad)) {
            Ext.callback(me.manageAfterLoad);
            me.manageAfterLoad = null;
        }
    },

    addFinishEditingButton : function(cmp, consolidationTab) {
        var me = this, toolbar = me.getMainToolbar();
        if (!toolbar.down("[cls=finishEditingButton]")) {
            //toolbar.add("->");
            me.finishEditBtn = toolbar.insert(6, {
                cls : "finishEditingButton",
                margin : "0 10 0 240",
                text : "Finish consolidation",
                listeners : {
                    click : Ext.bind(me.stopConsolidation, me, [cmp, consolidationTab])
                }
            });
        }
    }
});
