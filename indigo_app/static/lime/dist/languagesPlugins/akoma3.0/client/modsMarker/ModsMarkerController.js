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

Ext.define('LIME.controller.ModsMarkerController', {
    extend : 'Ext.app.Controller',

    views : ['LIME.ux.modsMarker.ModsMarkerWindow'],

    refs : [{
        ref : 'contextMenu',
        selector : 'contextMenu'
    },{
        selector : 'appViewport',
        ref : 'appViewport'
    },{
        selector: 'modsMarkerWindow',
        ref: 'modsWindow'
    },{
        selector: 'modsMarkerWindow textfield[name=selection]',
        ref: 'selectionField'
    }],
    
    config: {
        pluginName: "modsMarker",
        renumberingAttr: "renumbering",
        joinAttr: "joined",
        splitAttr: "splitted",
        externalConnectedElements: ["quotedStructure", "quotedText", "ref", "rref", "mref"]
    },


    init : function() {
        var me = this;
        this.control({
            '#secondEditor mainEditor' : {
                click: me.secondEditorClickHandler
            }
        });
    },

    secondEditorClickHandler: function(editor, evt) {
        var selectedNode = DomUtils.getFirstMarkedAncestor(evt.target);
        Ext.callback(this.secondEditorClickHandlerCustom, this, [selectedNode, evt, editor]);
    },
    
    onDocumentLoaded : function(docConfig) {
        var me = this, modPosChecked = Ext.bind(this.modPosChecked, this);
        this.addModificationButtons();
        
        this.posMenu = {
            items : [{
                type: "start"
            },{
                type: "before"
            },{
                type: "inside"
            },{
                type: "after"
            },{
                type: "end"
            },{
                type: "unspecified"
            }]
        };
        
        Ext.each(this.posMenu.items, function(item) {
            item.text = Locale.getString(item.type, me.getPluginName());
            item.checkHandler = modPosChecked;
            item.group = "modPos";
            item.checked = false;
        });
        
        try {
            this.detectExistingMods();    
        } catch(e) {
            Ext.log({level: "error"}, e);
        }
    },
    
    modPosChecked: function(cmp, checked) {
        var me = this, language = me.getController("Language"), 
            typesMenu = cmp.up("*[name=types]"),
            pos, destination;
        if(checked && typesMenu && typesMenu.textMod) {
            destination = typesMenu.textMod.querySelector('*[class="destination"]');
            if(destination) {
                pos = language.nodeGetLanguageAttribute(destination, "pos");  
                destination.setAttribute(pos.name, cmp.type);             
            }
        }
    },
    
    detectExistingMods: function(noEffect) {
        var me = this, editor = me.getController("Editor"), 
            editorBody = editor.getBody(),
            docMeta = me.getDocumentMetadata(),
            langPrefix = docMeta.langPrefix,
            language = me.getController("Language"),
            metaDom = docMeta.metadata.originalMetadata.metaDom,
            button = DocProperties.getFirstButtonByName("mod"),
            modsElements = editorBody.querySelectorAll("*[" + DomUtils.elementIdAttribute + "][class~='mod']"),
            returnMods = [],
            hrefAttr = langPrefix+"href";
        
        Ext.each(modsElements, function(element) {
            var elId = language.nodeGetLanguageAttribute(element, "eId"),
                intId = element.getAttribute(DomUtils.elementIdAttribute),
                metaMod, textMod, modType, buttonCfg;
            if (elId.value) {
                metaMod = metaDom.querySelector('*[class="source"]['+langPrefix+'href="'+elId.value+'"], *[class="source"]['+langPrefix+'href="#'+elId.value+'"]');
            } else {
                metaMod = metaDom.querySelector('*[class="source"]['+langPrefix+'href="'+intId+'"], *[class="source"]['+langPrefix+'href="#'+intId+'"]');
            }
            if(metaMod) {
                textMod = metaMod.parentNode;
                modType = textMod.getAttribute('type');
                if(!noEffect) {
                    metaMod.setAttribute(langPrefix+'href', "#"+intId);
                    element.removeAttribute(elId.name);
                }
                returnMods.push({
                    node: element,
                    type: modType,
                    textMod: textMod
                });
                if(modType) {
                    buttonCfg = Ext.Object.getValues(me.activeModButtons).filter(function(cfg) {
                        return cfg.modType == modType;
                    })[0];
                    if(buttonCfg && !noEffect) {
                        me.setElementStyles([element], button, null, buttonCfg);   
                    }
                }
            }
        });
        
        
        modsElements = metaDom.querySelectorAll("[class=passiveModifications] [class=textualMod]");
        Ext.each(modsElements, function(element) {
            var modEls = element.querySelectorAll("["+hrefAttr+"]");
            var modType = element.getAttribute('type');
            if(modType) {
                var buttonCfg = Ext.Object.getValues(me.passiveModButtons).filter(function(cfg) {
                    return cfg.modType == modType;
                })[0];
                if(buttonCfg) {
                    button = DocProperties.getFirstButtonByName(buttonCfg.markAsButton);
                }
                Ext.each(modEls, function(modEl) {
                    var href = modEl.getAttribute(hrefAttr);
                    if(!Ext.isEmpty(href.trim())) {
                        var id = (href.charAt(0) == "#") ? href.substring(1) : href;
                        var editorEl = editorBody.querySelector("*[" + langPrefix + "eid='"+id+"']");
                        if(editorEl && !noEffect) {
                            var edElId = editorEl.getAttribute(DomUtils.elementIdAttribute);
                            modEl.setAttribute(hrefAttr, href.replace(id, edElId));
                            editorEl.removeAttribute(hrefAttr);
                            if ( element.querySelector('.old') )  {
                                var oldText = element.querySelector('.old').textContent;
                                editorEl.setAttribute('data-old-text', oldText);
                                if ( modType == 'repeal' ) {
                                    editorEl.innerHTML = oldText;
                                }
                            }
                            if(buttonCfg && button && DomUtils.getButtonByElement(editorEl).name == button.name) {
                                me.setElementStyles([editorEl], button, null, buttonCfg);
                            }
                        }
                    }
                });
            }
        });

        //TODO:passive mods
        return returnMods;
    },
    
    beforeContextMenuShow: function(menu, node) {
        var me = this, elementName = DomUtils.getElementNameByNode(node),
            markedParent, language = me.getController("Language"),
            button = DomUtils.getButtonByElement(node);
        if(!elementName) {
            node = DomUtils.getFirstMarkedAncestor(node.parentNode);
            button = DomUtils.getButtonByElement(node);
            elementName = DomUtils.getElementNameByNode(node);
        }
        if(button && button.name == 'ref') {
            if(!menu.down("*[name=openlink]"))
                menu.add({
                    text : 'Resolve link',
                    name: 'openlink',
                    refNode: node,
                    handler : function() {
                        var href = node.getAttribute('akn_href');
                        if (href && href.length > 3) {
                            window.open('http://akresolver.cs.unibo.it/akn' + href);
                        }
                    }
                });
        }
        
        if(node && elementName) {
            markedParent = DomUtils.getFirstMarkedAncestor(node.parentNode);
            if(markedParent && (elementName == "quotedStructure"
                || elementName == "quotedText") && DomUtils.getElementNameByNode(markedParent) == "mod" ) {
                    
                var textMod = me.detectModifications(markedParent, false, false, true);
                textMod = (textMod) ? textMod.textMod : null;
                if(textMod && textMod.getAttribute("type") == "substitution") {
                    var href = language.nodeGetLanguageAttribute(node, "href"),
                        elId = node.getAttribute(DomUtils.elementIdAttribute),
                        langId = language.nodeGetLanguageAttribute(node, "eid"),
                        modElement = textMod.querySelector("*[akn_href*="+elId+"], *[akn_href*="+langId.value+"]"),
                        modType = (modElement) ? modElement.getAttribute("class") : "",
                        destination = textMod.querySelector('*[class="destination"]'), pos,
                        posMenu = Ext.clone(me.posMenu), menuItem;
                        
                    if(destination) {
                        pos = language.nodeGetLanguageAttribute(destination, "pos");
                        if(pos.value) {
                            menuItem = posMenu.items.filter(function(item) {
                                return item.type == pos.value;
                            })[0];
                            if(menuItem) {
                                menuItem.checked = true;
                            }
                        }    
                    }

                    if(!menu.down("*[name=modType]")) {
                        menu.add(['-', {
                            text : 'Type',
                            name: "modType",
                            menu : {
                                name: "types",
                                textMod: textMod,
                                refNode: node,
                                modElement: modElement,
                                items : [{
                                    text : 'Old',
                                    group : 'modType',
                                    textMod: textMod,
                                    modElement: modElement,
                                    refNode: node,
                                    type: "old",
                                    checked: (modType == "old") ? true : false,
                                    checkHandler : Ext.bind(me.onTypeSelected, me)
                                }, {
                                    text : 'New',
                                    group : 'modType',
                                    checked: (modType == "new") ? true : false,
                                    textMod: textMod,
                                    refNode: node,
                                    modElement: modElement,
                                    type: "new",
                                    checkHandler : Ext.bind(me.onTypeSelected, me)
                                }, {
                                    text : 'Pos',
                                    group : 'modType',
                                    checked: (modType == "pos") ? true : false,
                                    type: "pos",
                                    checkHandler : Ext.bind(me.onTypeSelected, me),
                                    menu: posMenu
                                }]
                            }
                        }]);
                    }
                }
            } else if(elementName == "mod") {
                var meta = this.getAnalysisByNodeOrNodeId(node);
                if(meta && !menu.down("*[name=modType]")) {
                    var modType = meta.type;
                    menu.add(['-', {
                        text : 'Type',
                        name: "modType",
                        menu : {
                            items : [{
                                text : Locale.getString("insertion", me.getPluginName()),
                                modType: 'insertion',
                                group : 'modType',
                                refNode: node,
                                checked: (modType == "insertion") ? true : false,
                                checkHandler : Ext.bind(me.onModTypeSelected, me)
                            }, {
                                text : Locale.getString("repeal", me.getPluginName()),
                                modType: 'repeal',
                                group : 'modType',
                                refNode: node,
                                checked: (modType == "repeal") ? true : false,
                                checkHandler : Ext.bind(me.onModTypeSelected, me)
                            }, {
                                text : Locale.getString("substitution", me.getPluginName()),
                                modType: 'substitution',
                                group : 'modType',
                                refNode: node,
                                checked: (modType == "substitution") ? true : false,
                                checkHandler : Ext.bind(me.onModTypeSelected, me)
                            }]
                        }
                    }]);
                }
            }
            
            me.addPosMenuItems(menu, node, elementName, markedParent);
            me.addExternalContextMenuItems(menu, node, elementName, markedParent);
        }
    },
    
    
    addPosMenuItems: function(menu, node, elementName, markedParent) {
        var me = this, language = me.getController("Language"), cls, 
            mod = me.detectModifications(node, false, false, true);
            
        if(mod && mod.modElement) {
            cls = mod.modElement.getAttribute("class");
            if(cls == "destination" || cls == "source") {
                if(!menu.down("*[name=modPos]")) {
                    var posMenu = Ext.clone(me.posMenu);
                    var pos = language.nodeGetLanguageAttribute(mod.modElement, "pos");
                    if(pos.value) {
                        menuItem = posMenu.items.filter(function(item) {
                            return item.type == pos.value;
                        })[0];
                        if(menuItem) {
                            menuItem.checked = true;
                        }
                    }
                    posMenu.textMod = mod.textMod;
                    posMenu.name = "types";
                    menu.add(['-', {
                        name: "modPos",
                        text : 'Pos',
                        type: "pos",
                        menu: posMenu
                    }]);
                }    
            }
        }
    },
    
    addExternalContextMenuItems: function(menu, node, elementName, markedParent) {
        var me = this;
        if(Ext.Array.contains(me.getExternalConnectedElements(), elementName)) {
            if(!menu.down("*[name=connectExternal]")) {
                var mods = me.detectExistingMods(true),
                    items = [];
                Ext.each(mods, function(mod) {
                    items.push({
                        text : Locale.getString(mod.type, me.getPluginName()),
                        modType: mod.type,
                        group : 'connectExternal',
                        refMod: mod,
                        checked: false,
                        checkHandler : Ext.bind(me.onExternalConnect, me),
                        listeners: {
                            focus: Ext.bind(me.onFocusExternalMenuItem, me)
                        }
                    });
                });
                
                menu.add(['-', {
                    text : 'Set as external mod element',
                    name: "connectExternal",
                    menu : {
                        items : items
                    }
                }]);
            }
        }
    },
    
    onFocusExternalMenuItem: function(cmp) {
        this.application.fireEvent('nodeFocusedExternally', cmp.refMod.node, {
            select : true,
            scroll : true
        });
    },
    
    onExternalConnect: function(cmp, checked) {
        console.log(cmp, checked);
    },
    
    onModTypeSelected: function(cmp, checked) {
        var me = this, buttonCfg = Ext.Object.getValues(me.activeModButtons).filter(function(cfg) {
                return cfg.modType == cmp.modType;
            })[0];
        if(buttonCfg) {
            if(checked && cmp.refNode) {
                var meta = me.getAnalysisByNodeOrNodeId(cmp.refNode),
                    button = DocProperties.getFirstButtonByName("mod");
                meta.analysis.setAttribute("type", cmp.modType);
                me.setElementStyles([cmp.refNode], button, null, buttonCfg);
            } else if(!checked) {
                me.removeElementStyles(cmp.refNode, buttonCfg);
            }
        }
        
    },
    
    onTypeSelected: function(cmp, checked) {
        var me = this, sameType, oldType;
        if(checked && cmp.textMod && cmp.modElement) {
            oldType = cmp.modElement.getAttribute("class");
            sameType = cmp.textMod.querySelectorAll("*[class="+cmp.type+"]"); 
            if(sameType.length == 1) {
                sameType[0].setAttribute("class", oldType);
            }
            cmp.modElement.setAttribute("class", cmp.type);
            me.insertTextModChildInOrder(cmp.textMod, cmp.modElement);
        } else if(checked && cmp.textMod) {
            var languageController = me.getController("Language"),
                langPrefix = languageController.getLanguagePrefix(),
                elId = cmp.refNode.getAttribute(DomUtils.elementIdAttribute),
                existedEl = cmp.textMod.querySelector("*[class='"+cmp.type+"']["+langPrefix+"href='#']"),
                href = (elId) ? "#"+elId : "#";
                
            if(existedEl) {
                existedEl.setAttribute(langPrefix+"href", href);
            } else {
                var textModObj = {
                    name: cmp.type,
                    attributes: [{
                        name: langPrefix+"href",
                        value: href
                    }]
                };
                var modEl = me.objToDom(cmp.textMod.ownerDocument, textModObj);
                me.insertTextModChildInOrder(cmp.textMod, modEl);
            }
        }
    },
    
    removeElementStyles: function(node, buttonCfg) {
        if(node) {
            node.removeAttribute(buttonCfg.modType);    
        }
    },
    
    addModificationButtons: function() {      
       this.addActiveMofigicationButtons();
       this.addPassiveModificationButtons();
    },
    
    addPassiveModificationButtons: function() {
         var me = this, app = me.application;
            markerButtons = {
                passiveModifications: {
                    label: Locale.getString("passiveModifications", me.getPluginName()),
                    buttonStyle: "border-radius: 3px; background-color: #74BAAC;"
                },
                insertionCustom: {
                    label: Locale.getString("insertion", me.getPluginName()),
                    buttonStyle: "background-color:#DBEADC;border-radius:3px",
                    handler: me.beforeInsertionHandler
                },
                repealCustom: {
                    label: Locale.getString("repeal", me.getPluginName()),
                    buttonStyle: "background-color:#DBEADC;border-radius:3px",
                    handler: me.beforeDelHandler
                },
                substitutionCustom: {
                    label: Locale.getString("substitution", me.getPluginName()),
                    buttonStyle: "background-color:#DBEADC;border-radius:3px",
                    handler: me.beforeSubstitutionHandler,
                    elementStyle: "background-color: #fcf8e3;border-color: #faebcc;",
                    labelStyle: "border-color: #faebcc;",
                    shortLabel: Locale.getString("substitution", me.getPluginName()),
                    modType: "substitution"
                },
                splitCustom: {
                    label: Locale.getString("split", me.getPluginName()),
                    buttonStyle: "background-color:#DBEADC;border-radius:3px",
                    handler: function(button) {
                        if ( DocProperties.documentState == 'diffEditingScenarioB' ) { 
                            me.splitHandlerB(button);
                        } else {
                            me.splitHandler(button);
                        }
                    }
                },
                joinCustom: {
                    label: Locale.getString("join", me.getPluginName()),
                    buttonStyle: "background-color:#DBEADC;border-radius:3px",
                    handler: function(button) {
                        if ( DocProperties.documentState == 'diffEditingScenarioB' ) { 
                            me.joinHandlerB(button);
                        } else {
                            me.joinHandler(button);
                        }
                    }
                },
                renumberingCustom: {
                    label: Locale.getString("renumbering", me.getPluginName()),
                    buttonStyle: "background-color:#DBEADC;border-radius:3px",
                    handler: me.renumberingHandler
                },
                destintionText: {
                    label: Locale.getString("destinationText", me.getPluginName()),
                    buttonStyle: "border-radius: 3px; background-color: #74BAAC;"
                },
                action: {
                    label: Locale.getString("action", me.getPluginName()),
                    buttonStyle: "border-radius: 3px; background-color: #74BAAC;"
                }
            },
            rules = {
                elements: {
                    passiveModifications: {
                        //children: ["insertionCustom", "repealCustom", "substitutionCustom", "splitCustom", "joinCustom", "renumberingCustom"]
                        children: ["commonReference", "destintionText", "action"]
                    },
                    destintionText: {
                        children: ["quotedStructure", "quotedText"]
                    },
                    action: {
                        children: ["insertionCustom", "repealCustom", "substitutionCustom", "splitCustom", "joinCustom", "renumberingCustom"]
                    }
                }
            },
            config = {
                name : 'passiveModifications',
                group: "commons",
                after: "activeModifications",
                buttons: markerButtons,
                rules: rules,
                scope: me
            };
       app.fireEvent(Statics.eventsNames.addMarkingButton, config);
       me.passiveModButtons = markerButtons;
    },
    
    addActiveMofigicationButtons: function() {
        var me = this, app = me.application;
            markerButtons = {
                activeModifications: {
                    label: Locale.getString("activeModifications", me.getPluginName()),
                    buttonStyle: "border-radius: 3px; background-color: #74BAAC;"
                },
                insertionCustom: {
                    label: Locale.getString("insertion", me.getPluginName()),
                    buttonStyle: "background-color:#DBEADC;border-radius:3px",
                    handler: me.activeInsertionHandler,
                    elementStyle: "background-color: #dff0d8; border-color: #d6e9c6;",
                    labelStyle: "border-color: #d6e9c6;",
                    markAsButton: "mod",
                    shortLabel: Locale.getString("insertion", me.getPluginName()),
                    modType: "insertion"
                },
                repealCustom: {
                    label: Locale.getString("repeal", me.getPluginName()),
                    buttonStyle: "background-color:#DBEADC;border-radius:3px",
                    handler: me.activeDelHandler,
                    elementStyle: "background-color: #f2dede;border-color: #ebccd1;",
                    labelStyle: "border-color: #ebccd1;",
                    markAsButton: "mod",
                    shortLabel: Locale.getString("repeal", me.getPluginName()),
                    modType: "repeal"
                },
                substitutionCustom: {
                    label: Locale.getString("substitution", me.getPluginName()),
                    buttonStyle: "background-color:#DBEADC;border-radius:3px",
                    handler: me.activeSubstitutionHandler,
                    elementStyle: "background-color: #fcf8e3;border-color: #faebcc;",
                    labelStyle: "border-color: #faebcc;",
                    markAsButton: "mod",
                    shortLabel: Locale.getString("substitution", me.getPluginName()),
                    modType: "substitution"
                },
                splitCustom: {
                    label: Locale.getString("split", me.getPluginName()),
                    buttonStyle: "background-color:#DBEADC;border-radius:3px",
                    handler: me.activeSplitHandler,
                    elementStyle: "background-color: #D4E7ED; border-color: #74A6BD;",
                    labelStyle: "border-color: #74A6BD",
                    markAsButton: "mod",
                    shortLabel: Locale.getString("split", me.getPluginName()),
                    modType: "split"
                },
                joinCustom: {
                    label: Locale.getString("join", me.getPluginName()),
                    buttonStyle: "background-color:#DBEADC;border-radius:3px",
                    handler: me.activeJoinHandler,
                    elementStyle: "background-color: #AB988B; border-color: #B06A3B;",
                    labelStyle: "border-color: #B06A3B;",
                    markAsButton: "mod",
                    shortLabel: Locale.getString("join", me.getPluginName()),
                    modType: "join"
                },
                renumberingCustom: {
                    label: Locale.getString("renumbering", me.getPluginName()),
                    buttonStyle: "background-color:#DBEADC;border-radius:3px",
                    handler: me.activeRenumberingHandler,
                    elementStyle: "background-color: #EB8540; border-color: #AB988B;",
                    labelStyle: "border-color: #AB988B;",
                    markAsButton: "mod",
                    shortLabel: Locale.getString("renumbering", me.getPluginName()),
                    modType: "renumbering"
                },
                destintionText: {
                    label: Locale.getString("destinationText", me.getPluginName()),
                    buttonStyle: "border-radius: 3px; background-color: #74BAAC;"
                },
                action: {
                    label: Locale.getString("action", me.getPluginName()),
                    buttonStyle: "border-radius: 3px; background-color: #74BAAC;"
                }
            },
            rules = {
                elements: {
                    activeModifications: {
                        children: ["commonReference", "destintionText", "action"]
                    },
                    destintionText: {
                        children: ["quotedStructure", "quotedText"]
                    },
                    action: {
                        children: ["insertionCustom", "repealCustom", "substitutionCustom", "splitCustom", "joinCustom", "renumberingCustom"]
                    }
                }
            },
            config = {
                name : 'activeModifications',
                group: "commons",
                after: "commonReference",
                buttons: markerButtons,
                rules: rules,
                scope: me
            };
       app.fireEvent(Statics.eventsNames.addMarkingButton, config);
       me.activeModButtons = markerButtons;
    },
    
    getOrCreatePath: function(dom, path) {
        var me = this, elements = path.split("/"), node, 
            iterNode = dom, tmpNode;

        for(var i = 0; i<elements.length; i++) {
            iterNode = iterNode.querySelector("[class='"+elements[i]+"']");
            if(!iterNode) {
                iterNode = me.createMetaElement(dom, elements[i]);
            }
        }
        node = iterNode;
        return node;
    },
    
    createMetaElement: function(dom, name) {
        var me = this, node,
            metaStructure = Language.getMetadataStructure();
        var path = me.getElementStructurePath(name, metaStructure);
        if(path.length) {
            var iterNode = dom, tmpNode, parentStructure;
            Ext.each(path, function(objStructure) {
                if (iterNode.getAttribute("class") != objStructure.name) {
                    tmpNode = iterNode.querySelector("[class='" + objStructure.name + "']");
                    var source = (objStructure.name == 'analysis') ? {
                        attributes: [{
                            name: "source",
                            value: " "
                        }]
                    } : {};

                    if (!tmpNode) {
                        node = me.objToDom(iterNode.ownerDocument, Ext.merge({
                            name : objStructure.name
                        }, source));
                        me.insertChildInOrder(iterNode, node, parentStructure, objStructure);               
                    } else {
                        iterNode = tmpNode;
                    }
                }
                parentStructure = objStructure;
            }); 

        }
        return node;
    },
    
    
    getElementStructurePath: function(name, structure, inChildren) {
        var me = this, path = [], chPath = [];
        if(structure.name != name) {
            for(var i = 0; i<structure.children.length; i++) {
                chPath = me.getElementStructurePath(name, structure.children[i], structure.children);
                if(chPath.length) {
                    path = Ext.Array.merge([structure], chPath);
                    break;
                }
            }
        } else {
            path = [structure];
        }
        return path;
    },
    
    
    insertTextModChildInOrder: function(parent, child) {
        var me = this, txtModStructure = LoadPlugin.getSchemaElements(LoadPlugin.langSchema, "textualMod"),
            type = child.getAttribute("class"),
            childStructure = txtModStructure.children.filter(function(el) {return el.name == type;})[0];
        if(childStructure) {
            me.insertChildInOrder(parent, child, txtModStructure, childStructure);    
        }
    },
    
    insertChildInOrder: function(parent, child, parentStructure, childStructure) {
        var indexInParent = parentStructure.children.indexOf(childStructure),
            refNode, tmpNode;
        if(indexInParent == -1 || indexInParent == parentStructure.children.length-1) {
            parent.appendChild(child);
        } else {
            for(var i = indexInParent+1; i < parentStructure.children.length; i++) {
                refNode = parent.querySelector("[class='" + parentStructure.children[i].name + "']");
                if(refNode) break;
            }
            if(refNode) {
                parent.insertBefore(child, refNode);
            } else {
                parent.appendChild(child);
            }
        }
    },
    
    getMetaDomPath: function(path) {
        var me = this,
            docMeta = me.getDocumentMetadata(),
            metaDom = docMeta.metadata.originalMetadata.metaDom;
        return me.getOrCreatePath(metaDom, path);
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
    
    getDocumentMetadata: function() {
        var me = this, editor = me.getController("Editor"),
            languageController = me.getController("Language"),
            langPrefix = languageController.getLanguagePrefix(),
            metadata = editor.getDocumentMetadata();
        return {
            langPrefix: langPrefix,
            metadata: metadata
        };
    },
    
    setElementStyles: function(markedElements, button, originalButton, buttonCfg) {
        var me = this, editor = me.getController("Editor"), 
            styleClass = markedElements[0].getAttribute("class"),
            style = Ext.clone(button.pattern.wrapperStyle);
            
        buttonCfg = buttonCfg || me.activeModButtons[originalButton.name];
        Ext.each(markedElements, function(markedElement) {
            markedElement.setAttribute(buttonCfg.modType, "true");
        });
        
        style["this"]+= ";"+buttonCfg.elementStyle;
        style["before"]+= ";"+buttonCfg.labelStyle;
        editor.applyAllStyles('body#tinymce:not(.noboxes) *[class="' + styleClass + '"]['+buttonCfg.modType+']', style, buttonCfg.shortLabel);
    },

    getTextualModId: function( parent ) {
        var textualMods = parent.querySelectorAll("*[class~=textualMod]");
        return "pmod_"+(textualMods.length+1);
    },
    
    activeInsertionHandler: function(button, markedElements, originalButton) {
        if(!markedElements.length) return;
        var me = this,
            docMeta = me.getDocumentMetadata(),
            langPrefix = docMeta.langPrefix,
            metaDom = docMeta.metadata.originalMetadata.metaDom,
            activeModifications = me.getOrCreatePath(metaDom, "analysis/activeModifications"),
            modEl = markedElements[0], 
            quotedEl = modEl.querySelector("*[class~=quotedStructure], *[class~=quotedText]"),
            refEl = Array.prototype.slice.call(modEl.querySelectorAll("*[class~=ref]")).filter(function(el) {
                return (modEl == DomUtils.getFirstMarkedAncestor(el.parentNode));
            })[0],
            newHref = (quotedEl) ? quotedEl.getAttribute(DomUtils.elementIdAttribute) : "",
            destHref = (refEl) ? refEl.getAttribute(langPrefix+"href") : "";

        var textModObj = {
            name: "textualMod",
            attributes: [{
                name: "type",
                value: "insertion"
            },{
                name: "period",
                value: "#"
            },{
                name: "eId",
                value: me.getTextualModId(activeModifications)
            }],
            children: [{
                name: "source",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+modEl.getAttribute(DomUtils.elementIdAttribute)
                }]
            },{
                name: "destination",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+destHref
                }]
            },{
                name: "new",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+newHref
                }]
            }]
        };
        textualMod = me.objToDom(metaDom.ownerDocument, textModObj);
        activeModifications.appendChild(textualMod);
        me.setElementStyles(markedElements, button, originalButton);
        me.askForRenumbering(modEl, textualMod);
    },
    
    activeDelHandler: function(button, markedElements, originalButton) {
        if(!markedElements.length) return;
        var me = this,
            docMeta = me.getDocumentMetadata(),
            langPrefix = docMeta.langPrefix,
            metaDom = docMeta.metadata.originalMetadata.metaDom,
            activeModifications = me.getOrCreatePath(metaDom, "analysis/activeModifications"),
            modEl = markedElements[0], 
            quotedEl = modEl.querySelector("*[class~=quotedStructure], *[class~=quotedText]"),
            refEl = Array.prototype.slice.call(modEl.querySelectorAll("*[class~=ref]")).filter(function(el) {
                return (modEl == DomUtils.getFirstMarkedAncestor(el.parentNode));
            })[0],
            newHref = (quotedEl) ? quotedEl.getAttribute(DomUtils.elementIdAttribute) : "",
            destHref = (refEl) ? refEl.getAttribute(langPrefix+"href") : "";
        
        var textModObj = {
            name: "textualMod",
            attributes: [{
                name: "type",
                value: "repeal"
            },{
                name: "period",
                value: "#"
            },{
                name: "eId",
                value: me.getTextualModId(activeModifications)
            }],
            children: [{
                name: "source",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+modEl.getAttribute(DomUtils.elementIdAttribute)
                }]
            },{
                name: "destination",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+destHref
                }]
            }]
        };
        textualMod = me.objToDom(metaDom.ownerDocument, textModObj);
        activeModifications.appendChild(textualMod);
        me.setElementStyles(markedElements, button, originalButton);
        me.askForRenumbering(modEl, textualMod);
    },
    
    activeSubstitutionHandler: function(button, markedElements, originalButton) {
        if(!markedElements.length) return;
        var me = this,
            docMeta = me.getDocumentMetadata(),
            langPrefix = docMeta.langPrefix,
            metaDom = docMeta.metadata.originalMetadata.metaDom,
            activeModifications = me.getOrCreatePath(metaDom, "analysis/activeModifications"),
            modEl = markedElements[0], 
            quotedEls = modEl.querySelectorAll("*[class~=quotedStructure], *[class~=quotedText]"),
            refEl = Array.prototype.slice.call(modEl.querySelectorAll("*[class~=ref]")).filter(function(el) {
                return (modEl == DomUtils.getFirstMarkedAncestor(el.parentNode));
            })[0],
            newHref = (quotedEls[0]) ? quotedEls[0].getAttribute(DomUtils.elementIdAttribute) : "",
            oldHref = (quotedEls[1]) ? quotedEls[1].getAttribute(DomUtils.elementIdAttribute) : "",
            destHref = (refEl) ? refEl.getAttribute(langPrefix+"href") : "";
        var textModObj = {
            name: "textualMod",
            attributes: [{
                name: "type",
                value: "substitution"
            },{
                name: "period",
                value: "#"
            },{
                name: "eId",
                value: me.getTextualModId(activeModifications)
            }],
            children: [{
                name: "source",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+modEl.getAttribute(DomUtils.elementIdAttribute)
                }]
            },{
                name: "destination",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+destHref
                }]
            },{
                name: "old",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+oldHref
                }]
            },{
                name: "new",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+newHref
                }]
            }]
        };
        textualMod = me.objToDom(metaDom.ownerDocument, textModObj);
        activeModifications.appendChild(textualMod);
        me.setElementStyles(markedElements, button, originalButton);
        me.askForRenumbering(modEl, textualMod);
    },
    
    activeJoinHandler: function(button, markedElements, originalButton) {
        if(!markedElements.length) return;
        var me = this,
            docMeta = me.getDocumentMetadata(),
            langPrefix = docMeta.langPrefix,
            metaDom = docMeta.metadata.originalMetadata.metaDom,
            activeModifications = me.getOrCreatePath(metaDom, "analysis/activeModifications"),
            modEl = markedElements[0], 
            quotedEls = modEl.querySelectorAll("*[class~=quotedStructure], *[class~=quotedText]"),
            refEl = Array.prototype.slice.call(modEl.querySelectorAll("*[class~=ref]")).filter(function(el) {
                return (modEl == DomUtils.getFirstMarkedAncestor(el.parentNode));
            })[0],
            newHref = (quotedEls[0]) ? quotedEls[0].getAttribute(DomUtils.elementIdAttribute) : "",
            oldHref = (quotedEls[1]) ? quotedEls[1].getAttribute(DomUtils.elementIdAttribute) : "",
            destHref = (refEl) ? refEl.getAttribute(langPrefix+"href") : "";

        var textModObj = {
            name: "textualMod",
            attributes: [{
                name: "type",
                value: "join"
            },{
                name: "period",
                value: "#"
            },{
                name: "eId",
                value: me.getTextualModId(activeModifications)
            }],
            children: [{
                name: "source",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+modEl.getAttribute(DomUtils.elementIdAttribute)
                }]
            },{
                name: "destination",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+destHref
                }]
            },{
                name: "old",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+oldHref
                }]
            },{
                name: "new",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+newHref
                }]
            }]
        };
        textualMod = me.objToDom(metaDom.ownerDocument, textModObj);
        activeModifications.appendChild(textualMod);
        me.setElementStyles(markedElements, button, originalButton);
        me.askForRenumbering(modEl, textualMod);
    },
    
    activeSplitHandler: function(button, markedElements, originalButton) {
        if(!markedElements.length) return;
        var me = this,
            docMeta = me.getDocumentMetadata(),
            langPrefix = docMeta.langPrefix,
            metaDom = docMeta.metadata.originalMetadata.metaDom,
            activeModifications = me.getOrCreatePath(metaDom, "analysis/activeModifications"),
            modEl = markedElements[0], 
            quotedEls = modEl.querySelectorAll("*[class~=quotedStructure], *[class~=quotedText]"),
            refEl = Array.prototype.slice.call(modEl.querySelectorAll("*[class~=ref]")).filter(function(el) {
                return (modEl == DomUtils.getFirstMarkedAncestor(el.parentNode));
            })[0],
            newHref = (quotedEls[0]) ? quotedEls[0].getAttribute(DomUtils.elementIdAttribute) : "",
            oldHref = (quotedEls[1]) ? quotedEls[1].getAttribute(DomUtils.elementIdAttribute) : "",
            destHref = (refEl) ? refEl.getAttribute(langPrefix+"href") : "";
        

        var textModObj = {
            name: "textualMod",
            attributes: [{
                name: "type",
                value: "split"
            },{
                name: "period",
                value: "#"
            },{
                name: "eId",
                value: me.getTextualModId(activeModifications)
            }],
            children: [{
                name: "source",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+modEl.getAttribute(DomUtils.elementIdAttribute)
                }]
            },{
                name: "destination",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+destHref
                }]
            },{
                name: "old",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+oldHref
                }]
            },{
                name: "new",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+newHref
                }]
            }]
        };
        textualMod = me.objToDom(metaDom.ownerDocument, textModObj);
        activeModifications.appendChild(textualMod);
        me.setElementStyles(markedElements, button, originalButton);
        me.askForRenumbering(modEl, textualMod);
    },
    
    activeRenumberingHandler: function(button, markedElements, originalButton) {
        if(!markedElements.length) return;
        var me = this,
            docMeta = me.getDocumentMetadata(),
            langPrefix = docMeta.langPrefix,
            metaDom = docMeta.metadata.originalMetadata.metaDom,
            activeModifications = me.getOrCreatePath(metaDom, "analysis/activeModifications"),
            modEl = markedElements[0], 
            quotedEls = modEl.querySelectorAll("*[class~=quotedStructure], *[class~=quotedText]"),
            refEl = Array.prototype.slice.call(modEl.querySelectorAll("*[class~=ref]")).filter(function(el) {
                return (modEl == DomUtils.getFirstMarkedAncestor(el.parentNode));
            })[0],
            newHref = (quotedEls[0]) ? quotedEls[0].getAttribute(DomUtils.elementIdAttribute) : "",
            oldHref = (quotedEls[1]) ? quotedEls[1].getAttribute(DomUtils.elementIdAttribute) : "",
            destHref = (refEl) ? refEl.getAttribute(langPrefix+"href") : "";
        

        var textModObj = {
            name: "textualMod",
            attributes: [{
                name: "type",
                value: "renumbering"
            },{
                name: "period",
                value: "#"
            },{
                name: "eId",
                value: me.getTextualModId(activeModifications)
            }],
            children: [{
                name: "source",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+modEl.getAttribute(DomUtils.elementIdAttribute)
                }]
            },{
                name: "destination",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+destHref
                }]
            },{
                name: "old",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+oldHref
                }]
            },{
                name: "new",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+newHref
                }]
            }]
        };
        textualMod = me.objToDom(metaDom.ownerDocument, textModObj);
        activeModifications.appendChild(textualMod);
        me.setElementStyles(markedElements, button, originalButton);
    },

    beforeInsertionHandler: function() {
        var me = this,
            editor = me.getController('Editor'),
            selectionRange = editor.lastSelectionRange || editor.getEditor().selection.getRng();

        if ( selectionRange.toString() ) {
            var aliasButton = DocProperties.getFirstButtonByName('ins');
            me.application.fireEvent('markingMenuClicked', aliasButton, {
                callback : Ext.bind(me.insertionHandler, me)
            });
        } else {
            var focusedNode = editor.getFocusedNode();
                
            if ( focusedNode ){
                var button = DomUtils.getButtonByElement(focusedNode);
                me.insertionHandler(button, [focusedNode]);
                me.setElementStyles([focusedNode], button, button, {
                    shortLabel: button.shortLabel+" "+Locale.getString("inserted", me.getPluginName()),
                    modType: 'inserted',
                    elementStyle: "",
                    labelStyle: "background-color: #75d6ff; border: 1px solid #44b4d5;"
                });
            }
        }
    },
        
    insertionHandler: function(button, markedElements) {
        var me = this,
            docMeta = me.getDocumentMetadata(),
            langPrefix = docMeta.langPrefix,
            metaDom = docMeta.metadata.originalMetadata.metaDom,
            passiveModifications = me.getOrCreatePath(metaDom, "analysis/passiveModifications"),
            modEl;

        Ext.each(markedElements, function(element) {
            var textModObj = {
                name: "textualMod",
                attributes: [{
                    name: "type",
                    value: "insertion"
                },{
                    name: "period",
                    value: "#"
                },{
                    name: "eId",
                    value: me.getTextualModId(passiveModifications)
                }],
                children: [{
                    name: "source",
                    attributes: [{
                        name: langPrefix+"href",
                        value: " "
                    }]
                },{
                    name: "destination",
                    attributes: [{
                        name: langPrefix+"href",
                        value: "#"+element.getAttribute("internalid")
                    }]
                }]
            }; 
            textualMod = me.objToDom(metaDom.ownerDocument, textModObj);
            modEl = element;
            passiveModifications.appendChild(textualMod);
        });
        if ( DocProperties.documentState != 'diffEditingScenarioB' ) {
            me.askForRenumbering(modEl, textualMod);
        }
    },
    
    renumberingHandler: function(button) {
        var me = this, editor = me.getController("Editor"),
            selectedNode = editor.getSelectedNode(true);
        
        var num = Ext.Array.toArray(selectedNode.querySelectorAll(".num")).filter(function(num) {
            return num.parentNode == selectedNode;
        })[0];
        
        if(num) {
            me.createRenumbering(num, null, false, selectedNode);
        } else {
            Ext.MessageBox.alert("Error", "Number to renumbering is missing!");
        }
        
    },
    
    splitHandler: function(button) {
        var me = this, editor = me.getController("Editor"),
            selection = editor.getSelectionObject(null, null, true),
            node = DomUtils.getFirstMarkedAncestor(selection.node),
            formTitle = "Select the element to split", button;

        if(node && selection.start == selection.node && selection.node == selection.start) {
            // Save a reference of the selection
            editor.getBookmark();
            selection = editor.getSelectionObject();
            if(selection.start) {
                Ext.fly(selection.start).addCls("visibleBookmark");
                var parents = DomUtils.getMarkedParents(selection.start, function(parent) {
                    if(!DomUtils.getFirstMarkedAncestor(parent.parentNode)) {
                        return false;
                    }
                    return true;
                });
                if (parents.length) {
                    /*var elementSelector = {
                        xtype: 'radiogroup',
                        //columns: 1,
                        items: parents.reverse().map(function(parent) {
                            var id = parent.getAttribute(DomUtils.elementIdAttribute),
                                relBtn = DomUtils.getButtonByElement(parent);
                            return {
                                boxLabel: relBtn.shortLabel,
                                name: 'splitParent',
                                inputValue: id
                            };
                        })
                    };*/

                    // Work around for Extjs4 bug with radio buttons in window
                    var html = '';
                    var items = parents.reverse().map(function(parent) {
                        var id = parent.getAttribute(DomUtils.elementIdAttribute),
                            relBtn = DomUtils.getButtonByElement(parent);
                        
                        return {
                            boxLabel: relBtn.shortLabel,
                            name: 'splitParent',
                            inputValue: id
                        };
                    });
                    Utilities.getLastItem(items).checked = true;

                    Ext.each(items, function(item) {
                        var checked = (item.checked) ? 'checked="checked"' : '';
                        html+= '<input type="radio" name="'+item.name+'" value="'+item.inputValue+'">'+item.boxLabel+'<br>';
                    });

                    var elementSelector = {
                        xtype  : 'box',
                        autoEl : {
                            html : html
                        }
                    };

                    var onClose = function(cmp) {
                        cmp.close();
                        Ext.fly(selection.start).removeCls("visibleBookmark");
                    };

                    me.createAndShowFloatingForm(selection.start, formTitle, false, false, function(cmp) {
                        //var parentId = cmp.getValues().splitParent;
                        var parentId = me.getRadioSelectedValue("splitParent");
                        var tmpParent = Ext.fly(selection.start).parent(".toMarkNode", true) || 
                                        Ext.fly(selection.start).parent(".beaking", true);
                        var posNode = tmpParent || selection.start;
                        me.splitElement(DocProperties.getMarkedElement(parentId).htmlElement, posNode);
                        onClose(cmp);
                    }, onClose, {
                        items : [elementSelector],
                        width: 200
                    });
                } else {
                    Ext.fly(selection.start).removeCls("visibleBookmark");
                    Ext.MessageBox.alert("Error", "You can't split this element!");
                }
            }
        } else {
            Ext.MessageBox.alert("Error", "You can split one element at time!");
        } 
    },

    splitHandlerB: function(button) {
        //TODO
    },

    getRadioSelectedValue: function(name) {
        var inputItems = Ext.Array.toArray(document.getElementsByName(name));
        inputItems = inputItems.filter(function(input) {
            return input.checked;
        });
        return (inputItems.length) ? inputItems[0].value : false;
    },

    splitElement: function(node, posNode, initialSplitNode) {
        var me = this;
        initialSplitNode = initialSplitNode || node;
        if (posNode.parentNode == node) {
            var button = DomUtils.getButtonByElement(node);
            var newElement = Ext.DomHelper.createDom({
                 tag : node.tagName
            });
            DomUtils.insertAfter(newElement, node);
            while(posNode.nextSibling) {
                newElement.appendChild(posNode.nextSibling);
            }
            node.setAttribute(me.getSplitAttr(), "true");
            newElement.setAttribute(me.getSplitAttr(), "true");
            
            if(button) {
                me.setElementStyles([node, newElement], button, button, {
                    shortLabel: button.shortLabel+" "+Locale.getString("splitted", me.getPluginName()),
                    modType: me.getSplitAttr(),
                    elementStyle: "",
                    labelStyle: "background-color: #75d6ff; border: 1px solid #44b4d5;"
                });
                me.application.fireEvent('markingRequest', button, {
                    silent : true,
                    noEvent : true,
                    nodes : [newElement]
                });
                if(initialSplitNode == node) {
                    me.setSplitMetadata(node, newElement);
                }
            }
        } else if(node.compareDocumentPosition(posNode) & Node.DOCUMENT_POSITION_CONTAINED_BY) {
            me.splitElement(posNode.parentNode, posNode, initialSplitNode);
            me.splitElement(node, posNode.parentNode, initialSplitNode);
        }
    },
    
    setSplitMetadata: function(node1, node2) {
        var me = this,
            editorMeta = me.getDocumentMetadata(),
            langPrefix = editorMeta.langPrefix,
            language = me.getController("Language"),
            metaDom = editorMeta.metadata.originalMetadata.metaDom,
            passiveModifications = me.getOrCreatePath(metaDom, "analysis/passiveModifications"),
            prevId = language.nodeGetLanguageAttribute(node1, "eId").value || node1.getAttribute(DomUtils.elementIdAttribute),
            expressionThis = metaDom.querySelector("[class=FRBRExpression] [class=FRBRthis]");
            
        var prevId = (expressionThis && expressionThis.getAttribute("value")) 
                ? expressionThis.getAttribute("value")+"#"+prevId : "#"+prevId;
            
        textModObj = {
            name: "textualMod",
            attributes: [{
                name: "type",
                value: "split"
            },{
                name: "period",
                value: "#"
            },{
                name: "eId",
                value: me.getTextualModId(passiveModifications)
            }],
            children: [{
                name: "source",
                attributes: [{
                    name: langPrefix+"href",
                    value: " "
                }]
            },{
                name : "destination",
                attributes : [{
                    name : langPrefix + "href",
                    value : "#" + node1.getAttribute(DomUtils.elementIdAttribute)
                }]
            },{
                name : "destination",
                attributes : [{
                    name : langPrefix + "href",
                    value : "#" + node2.getAttribute(DomUtils.elementIdAttribute)
                }]
            },{
                name: "previous",
                attributes: [{
                    name: langPrefix+"href",
                    value: prevId
                },{
                    name: langPrefix+"showAs",
                    value: "previous"
                }]
            }, {
                name: "old",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+node1.getAttribute(DomUtils.elementIdAttribute)
                }]
            }]
        };

        textualMod = me.objToDom(metaDom.ownerDocument, textModObj);
        passiveModifications.appendChild(textualMod);   
    },
    
    joinHandler: function(button) {
        var me = this, editor = me.getController("Editor"),
            selection = editor.getSelectionObject(null, null, true),
            language = me.getController("Language"),
            start = DomUtils.getFirstMarkedAncestor(selection.start),
            end = DomUtils.getFirstMarkedAncestor(selection.end),
            node = DomUtils.getFirstMarkedAncestor(selection.node),
            button, iternode, toUnmark = [], joinedData = [];
        
        if(start && end && node && start != end && start.parentNode == node && end.parentNode == node) {
            button = DomUtils.getButtonByElement(start);
            if(button) {
                joinedData.push({
                    id: start.getAttribute(DomUtils.elementIdAttribute),
                    langId: language.nodeGetLanguageAttribute(start, "eId").value
                });
                iternode = start.nextElementSibling;
                while(iternode) {
                    DomUtils.moveChildrenNodes(iternode, start, true);
                    if(DomUtils.getButtonByElement(iternode)) {
                        joinedData.push({
                            id: iternode.getAttribute(DomUtils.elementIdAttribute),
                            langId: language.nodeGetLanguageAttribute(iternode, "eId").value
                        });
                        toUnmark.push(iternode);    
                    }
                    if(iternode == end) {
                        break;
                    }
                    iternode = iternode.nextElementSibling;
                }
                start.setAttribute(me.getJoinAttr(), "true");
                me.setElementStyles([start], button, button, {
                    shortLabel: button.shortLabel+" "+Locale.getString("joined", me.getPluginName()),
                    modType: me.getJoinAttr(),
                    elementStyle: "",
                    labelStyle: "background-color: #75d6ff; border: 1px solid #44b4d5;"
                });
                me.application.fireEvent(Statics.eventsNames.unmarkNodes, toUnmark);
                me.setJoinMetadata(start, joinedData);
            }
        } else {
            Ext.MessageBox.alert("Error", "Select more than one siblings!");
        } 
    },

    joinHandlerB : function(button) {
        var me = this,
            editor = me.getController("Editor"),
            selection = editor.getSelectionObject(null, null, true),
            joinedNode = DomUtils.getFirstMarkedAncestor(selection.start),
            joinedData = [];

        if ( joinedNode ) {
            var markButton = DomUtils.getButtonByElement(joinedNode);

            var onClose = function(cmp) {
                cmp.close();
            };

            var registerJoin = function(data) {
                joinedNode.setAttribute(me.getJoinAttr(), "true");
                me.setElementStyles([joinedNode], markButton, markButton, {
                    shortLabel: markButton.shortLabel+" "+Locale.getString("joined", me.getPluginName()),
                    modType: me.getJoinAttr(),
                    elementStyle: "",
                    labelStyle: "background-color: #75d6ff; border: 1px solid #44b4d5;"
                });
                me.setJoinMetadata(joinedNode, data);
            };

            var winCmp = me.createAndShowFloatingForm(joinedNode, 'Select elements to join', false, false, function(cmp) {
                var grid = cmp.down('grid'),
                    data = [];
                grid.store.each(function(record) {
                    var node = cmp.editor.getBody().querySelector('['+DomUtils.elementIdAttribute+'='+record.get('id')+']');
                    data.push({
                        id: record.get('id'),
                        langId: record.get('eId'),
                        node: node
                    });
                });
                registerJoin(data);
                onClose(cmp);
            }, onClose, {
                items : [me.getNodesGridConfig()],
                width: 400
            });

            me.secondEditorClickHandlerCustom = function(node, evt, ed) {
                winCmp.editor = ed;
                if ( !node ) return;
                var markButton = DocProperties.getFirstButtonByName(DomUtils.getNameByNode(node)),
                    body = ed.getBody();

                if ( markButton && winCmp && winCmp.isVisible() ) {
                    var grid = winCmp.down('grid');

                    if ( !grid.store.getCount() ) {
                        editor.unFocusNodes(false, body);
                    } else {
                        var firstNode = body.querySelector('['+DomUtils.elementIdAttribute+'='+grid.store.getAt(0).get('id')+']');
                        if ( firstNode && DomUtils.getSiblingsFromNode(firstNode).indexOf(node) == -1 ) {
                            Ext.Msg.alert(Locale.strings.error, "You can join only sibling nodes");
                            return;
                        }
                    }

                    editor.setFocusStyle(node);

                    grid.store.loadData([{
                        name: markButton.shortLabel,
                        content: node.textContent,
                        id: node.getAttribute(DomUtils.elementIdAttribute),
                        eId: node.getAttribute(Language.getAttributePrefix()+'eid')
                    }], true);
                }
            };
        }
    },

    getNodesGridConfig: function() {
        return {
            xtype: 'gridpanel',
            store: Ext.create('Ext.data.Store', {
                fields:['name', 'content', 'id', 'eId'],
                data: []
            }),
            columns: [
                { text: 'Name',  dataIndex: 'name' },
                { text: 'Content', dataIndex: 'content', flex: 1 }, {
                    xtype : 'actioncolumn',
                    width : 30,
                    sortable : false,
                    menuDisabled : true,
                    items : [{
                        icon : 'resources/images/icons/delete.png',
                        tooltip : 'Remove',
                        handler : function(grid, rowIndex) {
                            grid.getStore().removeAt(rowIndex);
                        }
                    }]
                }
            ]
        };
    },
    
    setJoinMetadata: function(joinedNode, joinedData) {
        var me = this,
            editorMeta = me.getDocumentMetadata(),
            langPrefix = editorMeta.langPrefix,
            metaDom = editorMeta.metadata.originalMetadata.metaDom,
            passiveModifications = me.getOrCreatePath(metaDom, "analysis/passiveModifications"),
            destId = joinedNode.getAttribute(DomUtils.elementIdAttribute);
            
        textModObj = {
            name: "textualMod",
            attributes: [{
                name: "type",
                value: "join"
            },{
                name: "period",
                value: "#"
            },{
                name: "eId",
                value: me.getTextualModId(passiveModifications)
            }],
            children: [{
                name: "source",
                attributes: [{
                    name: langPrefix+"href",
                    value: " "
                }]
            },{
                name: "destination",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+destId
                }]
            }]
        };
        
        Ext.each(joinedData, function(joinedEl) {
            textModObj.children.push({
                name : "old",
                attributes : [{
                    name : langPrefix + "href",
                    value : "#" + joinedEl.langId || joinedEl.id
                }]
            });
        }); 

        textualMod = me.objToDom(metaDom.ownerDocument, textModObj);
        passiveModifications.appendChild(textualMod);    
    },

    beforeDelHandler: function() {
        var me = this,
            editor = me.getController('Editor'),
            selectionRange = editor.lastSelectionRange || editor.getEditor().selection.getRng();

        if ( selectionRange.toString() ) {
            var aliasButton = DocProperties.getFirstButtonByName('del');
            me.application.fireEvent('markingMenuClicked', aliasButton, {
                callback : Ext.bind(me.delHandler, me)
            });
        } else {
            var focusedNode = editor.getFocusedNode();
            if ( focusedNode ){
                var button = DomUtils.getButtonByElement(focusedNode);
                me.delHandler(button, [focusedNode]);
                focusedNode.setAttribute(Language.getAttributePrefix()+"status", "removed");
                DomUtils.removeChildren(focusedNode);
                me.setElementStyles([focusedNode], button, button, {
                    shortLabel: button.shortLabel+" "+Locale.getString("deleted", me.getPluginName()),
                    modType: 'deleted',
                    elementStyle: "",
                    labelStyle: "background-color: #75d6ff; border: 1px solid #44b4d5;"
                });
            }
        }
    },
    
    delHandler: function(button, markedElements) {
        var me = this,
            editorMeta = me.getDocumentMetadata(),
            langPrefix = editorMeta.langPrefix,
            metaDom = editorMeta.metadata.originalMetadata.metaDom,
            passiveModifications = me.getOrCreatePath(metaDom, "analysis/passiveModifications"),
            modEl;

        var setMetadata = function(oldText) {
            Ext.each(markedElements, function(element) {
                oldText = oldText || DomUtils.getTextOfNode(element);
                var textModObj = {
                    name: "textualMod",
                    attributes: [{
                        name: "type",
                        value: "repeal"
                    },{
                        name: "period",
                        value: "#"
                    },{
                        name: "eId",
                        value: me.getTextualModId(passiveModifications)
                    }],
                    children: [{
                        name: "source",
                        attributes: [{
                            name: langPrefix+"href",
                            value: " "
                        }]
                    },{
                        name: "destination",
                        attributes: [{
                            name: langPrefix+"href",
                            value: "#"+element.getAttribute("internalid")
                        }]
                    },{
                        name: "old",
                        text: oldText
                    }]
                }; 
                modEl = element;
                textualMod = me.objToDom(metaDom.ownerDocument, textModObj);
                passiveModifications.appendChild(textualMod);
            });
        };


        if ( DocProperties.documentState != 'diffEditingScenarioB' ) {
            setMetadata();
            me.askForRenumbering(modEl, textualMod);
        } else if ( markedElements.length ) {
            var formTitle = 'Insert the old text';
            me.createAndShowFloatingForm(markedElements[0], formTitle, false, false, function(cmp, text) {
                setMetadata(text);
                cmp.close();
            }, function(cmp) {
                cmp.close();
                Ext.fly(markedElements[0]).remove();
            });
        }
    },
    
    updateSubsMetadata: function(node, oldText) {
        var me = this, extNode = new Ext.Element(node),
            elId = extNode.dom.getAttribute(DomUtils.elementIdAttribute),
            editorMeta = me.getDocumentMetadata(),
            parent = extNode.up(".hcontainer"),
            parentId = (parent) ? parent.getAttribute(DomUtils.elementIdAttribute) : elId,
            langPrefix = editorMeta.langPrefix,
            metaDom = editorMeta.metadata.originalMetadata.metaDom,
            passiveModifications = me.getOrCreatePath(metaDom, "analysis/passiveModifications"),
            query = "*[class='textualMod'][type='substitution'] *[class='new']["+langPrefix+"href='#"+elId+"']",
            prevTextualMod = passiveModifications.querySelector(query), textualMod,
            textModObj = {};

        textModObj = {
            name: "textualMod",
            attributes: [{
                name: "type",
                value: "substitution"
            },{
                name: "period",
                value: "#"
            },{
                name: "eId",
                value: me.getTextualModId(passiveModifications)
            }],
            children: [{
                name: "source",
                attributes: [{
                    name: langPrefix+"href",
                    value: " "
                }]
            },{
                name: "destination",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+parentId
                }]
            },{
                name: "old",
                text: oldText
            },{
                name: "new",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+elId
                }]
            }]
        };
        
        textualMod = me.objToDom(metaDom.ownerDocument, textModObj);
        if(prevTextualMod) {
            prevTextualMod = prevTextualMod.parentNode;
            passiveModifications.replaceChild(textualMod, prevTextualMod);           
        } else {
            passiveModifications.appendChild(textualMod);    
        }
    },
    
    updateRenumberingMetadata: function(node, oldText, renumberedNode) {
        var me = this, extNode = new Ext.Element(node),
            language = me.getController("Language"),
            elId = language.nodeGetLanguageAttribute(renumberedNode, "eId").value || renumberedNode.getAttribute(DomUtils.elementIdAttribute),
            editorMeta = me.getDocumentMetadata(),
            parent = renumberedNode,
            parentId = (parent) ? parent.getAttribute(DomUtils.elementIdAttribute) : elId,
            langPrefix = editorMeta.langPrefix,
            metaDom = editorMeta.metadata.originalMetadata.metaDom,
            passiveModifications = me.getOrCreatePath(metaDom, "analysis/passiveModifications"),
            query = "*[class='textualMod'][type='renumbering'] *[class='destination']["+langPrefix+"href='#"+parentId+"']",
            prevTextualMod = passiveModifications.querySelector(query), textualMod,
            textModObj = {},    
            expressionThis = metaDom.querySelector("[class=FRBRExpression] [class=FRBRthis]");
            
        elId = (expressionThis && expressionThis.getAttribute("value")) 
                ? expressionThis.getAttribute("value")+"#"+elId : "#"+elId;
                
        textModObj = {
            name: "textualMod",
            attributes: [{
                name: "type",
                value: "renumbering"
            },{
                name: "period",
                value: "#"
            },{
                name: "eId",
                value: me.getTextualModId(passiveModifications)
            }],
            children: [{
                name: "source",
                attributes: [{
                    name: langPrefix+"href",
                    value: " "
                }]
            },{
                name: "destination",
                attributes: [{
                    name: langPrefix+"href",
                    value: "#"+parentId
                }]
            },{
                name: "previous",
                attributes: [{
                    name: langPrefix+"href",
                    value: elId
                },{
                    name: langPrefix+"showAs",
                    value: "previous"
                }]
            }]
        };
        
        textualMod = me.objToDom(metaDom.ownerDocument, textModObj);
        if(prevTextualMod) {
            prevTextualMod = prevTextualMod.parentNode;
            passiveModifications.replaceChild(textualMod, prevTextualMod);           
        } else {
            passiveModifications.appendChild(textualMod);    
        }
    },

    beforeSubstitutionHandler: function(aliasButton, elements) {
        var me = this,
            editor = me.getController('Editor'),
            selectionRange = editor.lastSelectionRange || editor.getEditor().selection.getRng();

        if ( selectionRange.toString() ) {
            var aliasButton = DocProperties.getFirstButtonByName('ins');
            me.application.fireEvent('markingMenuClicked', aliasButton, {
                callback : Ext.bind(me.substitutionHandler, me)
            });
        } else {
            var focusedNode = editor.getFocusedNode();
            if ( focusedNode ){
                var button = DomUtils.getButtonByElement(focusedNode);
                me.createSubstitutionBlock(focusedNode, false, false, function(obj) {
                    var oldText = DomUtils.getTextOfNode(obj.node);
                    me.updateSubsMetadata(focusedNode, oldText);

                    me.setElementStyles([focusedNode], button, button, {
                        shortLabel: button.shortLabel+" "+Locale.getString("replaced", me.getPluginName()),
                        modType: 'replaced',
                        elementStyle: "",
                        labelStyle: "background-color: #75d6ff; border: 1px solid #44b4d5;"
                    });
                });
            }
        }
    },
   
    substitutionHandler: function(aliasButton, elements, button) {
        this.createSubstitution(elements[0]);        
    },
    
    createRenumbering: function(node, formText, update, renumberedNode) {
        var me = this, editor = me.getController("Editor"),
            panel = me.createAndShowFloatingForm(node, "Insert the new text",formText, false, function(form, text) {
                var oldText = DomUtils.replaceTextOfNode(form.relatedNode, text);
                me.updateRenumberingMetadata(form.relatedNode, oldText, form.renumberedNode);
                form.renumberedNode.setAttribute(me.getRenumberingAttr(), oldText);
                var button = DomUtils.getButtonByElement(form.renumberedNode);
                me.setElementStyles([form.renumberedNode], button, button, {
                    shortLabel: button.shortLabel+" "+Locale.getString("renumbered", me.getPluginName()),
                    modType: me.getRenumberingAttr(),
                    elementStyle: "",
                    labelStyle: "background-color: #75d6ff; border: 1px solid #44b4d5;"
                });
                form.destroy();
                me.openedForm = null;
            }, function(form) {
                if(update) {
                    var oldText = DomUtils.replaceTextOfNode(form.relatedNode, form.originalText);
                    me.updateRenumberingMetadata(form.relatedNode, oldText, form.renumberedNode);                   
                } else {
                    //me.application.fireEvent(Statics.eventsNames.unmarkNodes, [form.relatedNode]);
                    //TODO: remove meta
                    form.renumberedNode.removeAttribute(me.getRenumberingAttr());   
                }
                form.destroy();
                me.openedForm = null;
            }); 

        editor.selectNode(node);
        panel.relatedNode = node;
        panel.renumberedNode = renumberedNode;
        panel.originalText = formText;
        me.openedForm = panel;
    },

    createSubstitutionBlock: function(node, formText, update, callback) {
        var me = this, editor = me.getController("Editor"),
            oldText = formText,
            button = DocProperties.getFirstButtonByName("ins");

        var panel = null;

        var onClose = function(cmp) {
            cmp.close();
        };

        panel = me.createAndShowFloatingForm(node, 'Select the element to replace', false, false, function(cmp) {
            var grid = cmp.down('grid'),
                data = [];
            grid.store.each(function(record) {
                var node = cmp.editor.getBody().querySelector('['+DomUtils.elementIdAttribute+'='+record.get('id')+']');
                data.push({
                    id: record.get('id'),
                    langId: record.get('eId'),
                    node: node
                });
            });
            Ext.callback(callback, me, [data[0]]);
            onClose(cmp);
        }, onClose, {
            items : [me.getNodesGridConfig()],
            width: 400
        });
        var firstEditorNode = node;
        me.secondEditorClickHandlerCustom = function(node, evt, ed) {
            panel.editor = ed;
            if ( !node ) return;
            var markButton = DocProperties.getFirstButtonByName(DomUtils.getNameByNode(node)),
                markButtonNameSecond = markButton.name,
                markButtonName = DomUtils.getNameByNode(firstEditorNode),
                body = ed.getBody();

            if ( markButtonNameSecond && panel && panel.isVisible() ) {
                if ( markButtonNameSecond != markButtonName ) {
                     Ext.Msg.alert(Locale.strings.error, "You need to select a "+markButtonName);
                     return;
                }
                var grid = panel.down('grid');

                if ( !grid.store.getCount() ) {
                    editor.unFocusNodes(false, body);
                }

                editor.setFocusStyle(node);

                grid.store.loadData([{
                    name: markButton.shortLabel,
                    content: node.textContent,
                    id: node.getAttribute(DomUtils.elementIdAttribute),
                    eId: node.getAttribute(Language.getAttributePrefix()+'eid')
                }], false);
            }
        };
    },
    
    createSubstitution: function(node, formText, update) {
        var me = this, editor = me.getController("Editor"),
            oldText = formText,
            button = DocProperties.getFirstButtonByName("ins");
            /*var panel = me.createAndShowFloatingForm(node, function(form, text) {
                var oldText = DomUtils.replaceTextOfNode(form.relatedNode, text);
                me.updateSubsMetadata(form.relatedNode, oldText);
                form.destroy();
                me.openedForm = null;
            }, function(form) {
                if(update) {
                    var oldText = DomUtils.replaceTextOfNode(form.relatedNode, form.originalText);
                    me.updateSubsMetadata(form.relatedNode, oldText);                   
                } else {
                    me.application.fireEvent(Statics.eventsNames.unmarkNodes, [form.relatedNode]);    
                }
                form.destroy();
                me.openedForm = null;
            }, formText);*/
        var panel = null;

        if ( DocProperties.documentState == 'diffEditingScenarioB' ) {
            var formTitle = 'Insert the old text';
            var formText = false;
            if ( update ) {
                formText = node.getAttribute('data-old-text');
            }
            me.createAndShowFloatingForm(node, formTitle, formText, false, function(cmp, text) {
                me.updateSubsMetadata(node, text);
                node.setAttribute('data-old-text', text);
                me.setElementStyles([node], button, null, me.passiveModButtons.substitutionCustom);
                cmp.close();
            }, function(cmp) {
                cmp.close();
                if ( !update ) {
                    DomUtils.unwrapNode(node);
                }
            });
        } else {
            if(!update) {
                //oldText = DomUtils.replaceTextOfNode(node, "  ");
                oldText = DomUtils.getTextOfNode(node);
                me.updateSubsMetadata(node, oldText);
                me.setElementStyles([node], button, null, me.passiveModButtons.substitutionCustom);
            }
            panel = me.createAndShowFloatingForm(node, "The old text", oldText, true);
            Ext.defer(function() {
                editor.getEditor().focus();
                if(!update) {
                    editor.selectNode(node);    
                }
            }, 40);
        }

        me.openedForm = panel;
    },
    
    createAndShowFloatingForm: function(node, title ,text, readOnly, onAccept, onCancel, customConfig) {
        customConfig = customConfig || {};
        var me = this, editor = me.getController("Editor"), 
            editorBoundingRect = editor.getIframe().dom.getBoundingClientRect(),
            elementBoundingRect = node.getBoundingClientRect(),
            boxMargin= {top: -150, left: -20},
            boxWidth = customConfig.width || 300,
            boxPos = {x: (editorBoundingRect.left+elementBoundingRect.left+boxMargin.left),
                      y: (editorBoundingRect.top+elementBoundingRect.top+boxMargin.top)},
            panel, buttons; 
        
        
        if(!readOnly) {
            buttons = [{
                text : Locale.getString("openFileWindowSouthCancelButtonLabel"),
                icon : 'resources/images/icons/cancel.png',
                handler : function() {
                    Ext.callback(onCancel, me, [this.up("form")]);
                }
            }, {
                text : Locale.getString("ok"),
                icon : 'resources/images/icons/accept.png',
                handler : function() {
                    var form = this.up("form");
                    if (form.getForm().isValid()) {
                        Ext.callback(onAccept, me, [form, form.getValues().newText]);
                    }
                }
            }];
        }
        panel = Ext.widget('form', {
            width : boxWidth,
            bodyPadding : 5,
            title : title,
            closable: true,
            floating : true,
            frame : true,
            layout : 'fit',
            items : customConfig.items || [{
                xtype : "textareafield",
                name : 'newText',
                readOnly: readOnly,
                grow : true,
                value: text || "",
                margin : 0,
                allowBlank: false
            }],
            
            buttons: buttons
        });
        
        if(elementBoundingRect.width) {
            if(elementBoundingRect.width < boxWidth) {
                boxPos.x -= (boxWidth -  elementBoundingRect.width)/2;    
            } else {
                boxPos.x += (elementBoundingRect.width - boxWidth)/2;
            }
        }
        panel.showAt(boxPos.x, boxPos.y);
        return panel;
    },
    
    substitutionUpdate: function(node, textMod) {
        var me = this, oldEl = textMod.querySelector("*[class='old']"),
            extEl = new Ext.Element(node), nodeText = DomUtils.getTextOfNode(node);
            
        //extEl.setHTML(DomUtils.getTextOfNode(oldEl));
        me.createSubstitution(node, DomUtils.getTextOfNode(oldEl), true);
    },
    
    getAnalysisByNodeOrNodeId: function(node, nodeId) {
        var me = this, id = nodeId || node.getAttribute(DomUtils.elementIdAttribute),
            editorMeta = me.getDocumentMetadata(),
            langPrefix = editorMeta.langPrefix,
            metaDom = editorMeta.metadata.originalMetadata.metaDom,
            metaEl = metaDom.querySelector("*["+langPrefix+"href='#"+id+"']");
        
        if(metaEl && metaEl.parentNode) {
            return {
                analysis: metaEl.parentNode,
                node: metaEl,
                type: metaEl.parentNode.getAttribute("type")
            };
        }
    },
    
    detectModifications: function(node, nodeId, unmarked, noAction) {
        var me = this, elId = nodeId || node.getAttribute(DomUtils.elementIdAttribute),
            editorMeta = me.getDocumentMetadata(),
            langPrefix = editorMeta.langPrefix,
            metaDom = editorMeta.metadata.originalMetadata.metaDom,
            textModChild = metaDom.querySelector("*["+langPrefix+"href='#"+elId+"']"),
            textMod, modType;

        if(textModChild && textModChild.parentNode) {
            textMod = textModChild.parentNode;
            modType= textMod.getAttribute('type');
            if(noAction) {
                return {
                    textMod: textMod,
                    modElement: textModChild
                };
            }

            if ( unmarked ) {
                me.unmarkModMeta(textMod);
                return;
            }

            switch(modType) {
                case "substitution":
                    if(textMod.parentNode.getAttribute("class") != "activeModifications"
                            && textModChild.getAttribute("class") == "new") {
                            me.substitutionUpdate(node, textMod);
                    }
                    break;
                case "insertion":
                    break;
                case "repeal":
                    break;
            }
        }
        
        return null;
    },

    unmarkModMeta: function(textModNode) {
        var modifications = textModNode.parentNode;
        modifications.removeChild(textModNode);

        if ( !modifications.childNodes.length ) {
            modifications.parentNode.removeChild(modifications);
        }
    },
    
    askForRenumbering: function(modEl, textualMod) {
        
        var me = this, win = Ext.widget("window", {
            title: "This modification has caused a renumbering?",
            closable: false,
            width: 300,
            modal: true,
            dockedItems : [{
                xtype : 'toolbar',
                dock : 'bottom',
                ui : 'footer',
                items : ['->', {
                    xtype : 'button',
                    icon : 'resources/images/icons/cancel.png',
                    text : "No",
                    handler: function() {
                        this.up("window").close();
                    }
                }, {
                    xtype : 'button',
                    icon : 'resources/images/icons/accept.png',
                    text : "Yes",
                    handler: function() {
                        this.up("window").close();
                        me.addRenumberingAfterMod(modEl, textualMod);
                    }
                }]
            }]
        }).show();
        /*Ext.Msg.confirm("Renumbering", "This modification has caused a renumbering?", function(response) {
            if(response == "yes") {
                console.log(modEl, textualMod);
            }
        }, this);*/
    },
    
    addRenumberingAfterMod: function(modEl, textualMod) {
        //TODO:
    },
    
    editorNodeFocused: function(node) {
        var me = this;
        if(me.openedForm) {
            me.openedForm.close();
            me.openedForm = null;
        }
        if(node) {
            try {
                me.detectModifications(node);    
            } catch(e) {
                Ext.log({level: "error"}, e);
            }
        }
    },
    
    nodesUnmarked: function(nodesIds) {
        var me = this;
        Ext.each(nodesIds, function(nodeId) {
            try {
                me.detectModifications(null, nodeId, true);
            } catch(e) {
                Ext.log({level: "error"}, e);
            }
        });
    },

    onRemoveController: function() {
        var me = this;
        me.application.removeListener(Statics.eventsNames.afterLoad, me.onDocumentLoaded, me);
        me.application.removeListener(Statics.eventsNames.editorDomNodeFocused, me.editorNodeFocused, me);
        me.application.removeListener(Statics.eventsNames.unmarkedNodes, me.nodesUnmarked, me);
    },
    
    onInitPlugin: function() {
        var me = this;
        me.application.on(Statics.eventsNames.afterLoad, me.onDocumentLoaded, me);
        me.application.on(Statics.eventsNames.editorDomNodeFocused, me.editorNodeFocused, me);
        me.application.on(Statics.eventsNames.unmarkedNodes, me.nodesUnmarked, me);
        me.application.fireEvent(Statics.eventsNames.registerContextMenuBeforeShow, Ext.bind(me.beforeContextMenuShow, me));
    }
});
