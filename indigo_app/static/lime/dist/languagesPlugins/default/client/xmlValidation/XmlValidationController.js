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

Ext.define('LIME.controller.XmlValidationController', {
    extend : 'Ext.app.Controller',

    views: ["LIME.view.Main", "LIME.ux.xmlValidation.ValidationResultWindow"],

    refs : [{
        ref : 'main',
        selector : 'main'
    },{
        ref: 'validationResult',
        selector: 'uxNotification [cls*=validationResult]' 
    },{
        ref: 'errorNumberText',
        selector: 'uxNotification [cls*=validationResult] text' 
    },{
        ref: 'moreInfoButton',
        selector: 'uxNotification [cls*=validationResult] #moreInfo'
    }, {
        ref: 'mainTabs',
        selector: 'main '
    }],

    config : {
        pluginName : "xmlValidation",
        errorsMappingFile: "errorsMapping.json"
    },

    onDocumentLoaded : function(docConfig) {
        var me = this;
        menu = {
            text : Locale.getString("validateXml", me.getPluginName()),
            tooltip : Locale.getString("validateXmlTooltip", me.getPluginName()),
            icon : 'resources/images/icons/accept.png',
            name : 'validateXml',
            handler : Ext.bind(this.beforeValidateXml, this)
        };
        me.application.fireEvent("addMenuItem", me, {
            menu : "documentMenuButton"
        }, menu);
    },

    beforeValidateXml: function() {
        var me = this;
        me.application.fireEvent(Statics.eventsNames.translateRequest, function(xml, aknIdMapping) {
            me.storeXmlData(xml, aknIdMapping);
            me.validateXml(xml);
        });
    },
    
    validateXml : function(xml) {
        var me = this, app = me.application, schema = Config.getLanguageSchemaPath(),
            // temporary solution
            aknVersion = xml.match('"http://docs.oasis-open.org/legaldocml/ns/akn/3.0/(CSD\\d\\d)"')[1];
        app.fireEvent(Statics.eventsNames.progressStart, null, {
            value : 0.2,
            text : " "
        });

        // temporary solution
        if(!Ext.isEmpty(aknVersion)) {
            schema = schema.replace(".xsd", "_"+aknVersion+".xsd");
        }

        Ext.Ajax.request({
            url : Utilities.getAjaxUrl(),
            method : 'POST',
            // send the content of the editor
            params : {
                requestedService : "XML_VALIDATION",
                source : xml,
                schema : schema
            },
            // the scope of the ajax request
            scope : this,
            success : this.onValidationResult,
            callback : function() {
                app.fireEvent(Statics.eventsNames.progressEnd);
            }
        });
    },

    onValidationResult: function(result) {
        var jsonData = Ext.decode(result.responseText, true);
        if(!jsonData) {
            jsonData = {
                decodeError : true
            };
        } else {
            // Zero based index to one based
            jsonData.line = jsonData.line + 1;
        }
        this.createResultWindow(jsonData);
    },

    storeXmlData: function(xml, aknIdMapping) {
        this.validatedXml = xml;
        this.xmlRows = xml.split('\n');
        this.aknIdMapping = aknIdMapping;
    },

    createResultWindow: function(errorData) {
        var errors = [].concat(errorData["fatal_error"])
                        .concat(errorData["error"])
                        .concat(errorData["warning"]).filter(function(el) {
                            return el != undefined;
                        });
        this.errorData = errors;

        if ( this.errorData.length ) {
            this.createErrorsResult();
        } else if ( errorData.started ) {
            this.createSuccessResult();
        }
    },

    createSuccessResult: function() {
        this.application.fireEvent(Statics.eventsNames.showNotification, {
            title : Locale.getString("validationSuccess", this.getPluginName()),
            content : Locale.getString("validationSuccess", this.getPluginName()),
            width : 200,
            status : true
        });

    },

    createErrorsResult: function() {
        var me = this,
            notification = this.getController('Notification');

        var items = this.errorData.map(function(item) {
            return me.buildErrorItemConfig(item);
        });


        this.numberIndicator = new Ext.Template("{nr}/{nrTot}");

        var cmp = notification.createNotificationWindow({
            title: new Ext.Template(me.getString("validateResultErrors")).apply({
                nr: items.length
            }),
            width : 400,
            draggable: true,
            spacing : 0,
            closeAction: 'destroy',
            layout: 'fit',
            items: {
                border: false,
                layout: 'card',
                cls: 'validationResult',
                activeItem: 0,
                height: 150,
                bbar: [{
                    text: me.getString("moreInfo"),
                    id: 'moreInfo',
                    enableToggle: true
                },'->', {
                    xtype: 'text',
                    text: this.numberIndicator.apply({
                        nr: 1,
                        nrTot: items.length
                    })
                },'->', {
                    text: me.getString("previous"),
                    id: 'card-prev'
                },{
                    text: me.getString("next"),
                    id: 'card-next'
                }],
                items: items
            }
        });

        cmp.show();
    },

    buildErrorItemConfig : function( item ) {
        var moreInfoTpl = new Ext.Template("<h4>{moreInfoHeader}</h4><span>{moreInfo}</span>"),
            moreInfoTextTpl = new Ext.Template(this.getString("moreInfoTpl")),
            simpleMessage = this.buildErrorHtml(item),
            technicalMessage = moreInfoTpl.apply({
                moreInfoHeader: this.getString("technicalInfo"),
                moreInfo: moreInfoTextTpl.apply(Ext.merge(Ext.clone(item), {
                    lineString: Ext.String.htmlEncode(item.lineString)
                }))
            });
            isAknPreview = this.getMainTabs().getActiveTab().xtype == "aknPreviewMainTab",
            mainMessage = isAknPreview ? technicalMessage : simpleMessage,
            secondaryMessage = isAknPreview ? simpleMessage : technicalMessage;

        return {
            xtype: 'panel',
            baseCls: 'x-panel-error',
            cls: 'goToElement',
            autoScroll: true,
            margin: 5,
            layout: {
                type:'vbox',
                padding:'5',
                align:'stretch'
            },
            defaults: {
                margin:'0 0 5 0',
                padding: 5
            },
            listeners: {
                afterrender: function(c) {
                    c.el.on('click', function() {
                        c.fireEvent('click', c);
                    });
                }
            },
            items:[{
                xtype: 'container',
                cls: 'errorsInfo',
                padding: 2,
                html: mainMessage
            },{
                xtype: 'container',
                cls: 'moreInfoPanel',
                hidden: true,
                html : secondaryMessage
            }]
        }
    },

    buildErrorHtml: function(config) {
        var name = this.findElementName(config), html = '',
            editorNode = (name) ? this.findEditorNode(name, config) : false,
            errorListTpl = new Ext.Template("<h4>{caption}</h4><ul>{errors}</ul>");
            //DocProperties.getFirstButtonByName('quotedText').shortLabel
        if ( this.errorsMapping && this.errorsMapping[config.code] ) {
            var errorConfig = this.errorsMapping[config.code],
                parent = ( editorNode ) ? DomUtils.getFirstMarkedAncestor(editorNode.parentNode) : false,
                parentName = (parent) ? DomUtils.getNameByNode(parent) : 
                            ( editorNode ) ? editorNode.parentNode.nodeName.toLowerCase() : false,
                nodeInfo = {
                    name : name,
                    parentName: (parentName) ? parentName : 'his wrapper'
                };

            var errorsHtml = '';
            var specificErrors = this.getSpecificErrors(nodeInfo, errorConfig);
            errorsHtml += new Ext.Template('<li>'+this.getString(errorConfig["genericError"])+'</li>').apply(nodeInfo);
            errorsHtml += this.buildSpecificErrorHtml(nodeInfo, specificErrors);

            html += errorListTpl.apply({
                caption: new Ext.Template(this.getString("element")).apply(nodeInfo),
                errors: errorsHtml
            });

            html += this.buildErrorTipsHtml(nodeInfo, specificErrors.reduce(function(tips, error) {
                return (error.tips && error.tips.length) ? tips.concat(error.tips) : tips
            }, []));
            return html;
        }

        return name;
    },

    getSpecificErrors: function(nodeInfo, config) {
        return (config.specificErrors) ? config.specificErrors.filter(function(error) {
            return error.elements.indexOf(nodeInfo.name) != -1;
        }) : [];
    },

    buildSpecificErrorHtml: function(nodeInfo, errors) {
        var me = this, html = "";
        return errors.reduce(function(html, errorConfig) {
            return html + new Ext.Template('<li>'+me.getString(errorConfig["error"])+'</li>').apply(nodeInfo);
        }, "");
    },

    buildErrorTipsHtml: function(nodeInfo, tips) {
        var me = this, html = "", 
            listTpl = new Ext.Template("<h4>{tipsCaption}</h4><ul>{tips}</ul>"),
            listItemTpl = new Ext.Template("<li>{tip}</li>");
        if ( tips && tips.length ) {
            var tipsHtml = tips.reduce(function(html, tip) {
                return html + listItemTpl.apply({
                    tip: new Ext.Template(me.getString(tip)).apply(nodeInfo)
                });
            }, "");

            html += listTpl.apply({
                tipsCaption: me.getString("tipsToResolveError"),
                tips: tipsHtml
            });
        }

        return html;
    },

    getString: function(name) {
        return Locale.getString(name, this.getPluginName())
    },

    onRemoveController: function() {
        var me = this;
        me.application.removeListener(Statics.eventsNames.afterLoad, me.onDocumentLoaded, me);
    },

    eventuallyDisableButton: function(btn) {
        var layout = btn.up('[cls*=validationResult]').getLayout();
        if ( (!layout.getPrev() && btn.id == 'card-prev') ||
             (!layout.getNext() && btn.id == 'card-next') ) {
            btn.disable();
        }
    },

    eventuallyEnableButton: function(btn) {
        var layout = btn.up('[cls*=validationResult]').getLayout();
        if ( (layout.getPrev() && btn.id == 'card-prev') ||
             (layout.getNext() && btn.id == 'card-next') ) {
            btn.enable();
        }
    },

    localizeElement: function(errorData) {
        var layout = this.getValidationResult().getLayout(),
            index = layout.getLayoutItems().indexOf(layout.activeItem),
            errorData = this.errorData[index];

        if (!errorData) return;

        var activeTab = this.getMain().getActiveTab();

        if ( activeTab.down('codemirror') ) {
            this.localizeRowInPreviewTab(activeTab, errorData);
        } else if ( activeTab.down('mainEditor') ) {
            this.localizeElementInEditor(errorData);
        }
    },

    localizeRowInPreviewTab: function( tab, errorData ) {
        var codemirrorCmp = tab.down('codemirror');

        if ( codemirrorCmp.getValue().trim() ) {
            codemirrorCmp.goToLine(errorData.line+2, true);
        }
    },

    localizeElementInEditor: function(errorData) {
        var elementName = this.findElementName(errorData),
            editorNode = (elementName) ? this.findEditorNode(elementName, errorData) : false;

        if ( editorNode ) {
            this.application.fireEvent(Statics.eventsNames.nodeFocusedExternally, editorNode, {
                select : true,
                scroll : true,
                click : true,
                highlight: true
            });
        }
    },

    findElementName: function(errorData) {
        var elNameRegex = new RegExp("^Element '{[^}]+}(\\w+)':");
        var name = errorData.message.match(elNameRegex);
        return (name && name.length == 2) ? name[1] : null;
    },

    findEditorNode: function(name, errorData) {
        var me = this, row = errorData.lineString || this.xmlRows[errorData.line],
            editorBody = this.getController('Editor').getBody(),
            editorNodes = editorBody.querySelectorAll('.'+name);

        if ( editorNodes.length == 1 ) return editorNodes[0];

        var idMatch = row.match(/eId="([^"]+)"/i);

        if ( idMatch && idMatch.length && me.aknIdMapping[idMatch[1]] ) {
            var node = editorBody.querySelector('['+DomUtils.elementIdAttribute+'="'+me.aknIdMapping[idMatch[1]]+'"]');
            if ( node ) return node;
        }

        //TODO: manage multiple occorences
        var range = DomUtils.findTextIgnoringHtml(row.trim(), editorBody).filter(function(range) {
                        return me.queryIncludingNode(range.startContainer, '.'+name) ? true : false;
                    })[0];

        return (range) ? me.queryIncludingNode(range.startContainer, '.'+name) : null;
    },

    queryIncludingNode: function(node, query) {
        return (Ext.fly(node).is(query)) ? node : node.querySelector(query);
    },

    setMoreInfoVisible: function(visible) {
        var winCmp = this.getValidationResult(),
            layout = winCmp.getLayout();

        if ( layout.activeItem && layout.activeItem.down('[cls*=moreInfoPanel]') ) {
            layout.activeItem.down('[cls*=moreInfoPanel]').setVisible(visible);
        }
    },

    downloadErrorsMapping: function() {
        var me = this, 
            url = Config.getPluginUrl(me.getPluginName());

        Ext.Ajax.request({
            url : url.relative+me.getErrorsMappingFile(),
            success : function(response, opts) {
                me.errorsMapping = Ext.decode(response.responseText, true);
            }
        });
    },
    
    init : function() {
        var me = this;
        __VAL = me;
        //Listening progress events
        this.application.on(Statics.eventsNames.afterLoad, this.onDocumentLoaded, this);
        
        me.downloadErrorsMapping();

        this.control({
            'uxNotification [cls*=validationResult]': {
                cardChanged: function(card, btn) {
                    me.eventuallyDisableButton(btn);
                    var windowCmp = btn.up('[cls*=validationResult]');
                    var otherBtn = windowCmp.query('#card-prev, #card-next').filter(function(cmp) {
                        return cmp != btn;
                    })[0];
                    
                    var indicator = this.numberIndicator.apply({
                        nr: windowCmp.getLayout().getLayoutItems().indexOf(card)+1,
                        nrTot: this.errorData.length
                    });

                    me.getErrorNumberText().setText(indicator);

                    me.eventuallyEnableButton(otherBtn);
                    me.getMoreInfoButton().toggle(false);
                    me.setMoreInfoVisible(false);
                }
            },
            'uxNotification [cls*=validationResult] #card-prev, [cls*=validationResult] #card-next': {
                afterrender: function(btn) {
                    me.eventuallyDisableButton(btn);
                }
            },
            'uxNotification [cls*=validationResult] #card-prev': {
                click: function(btn) {
                    var cmp = btn.up('[cls*=validationResult]'),
                        layout = cmp.getLayout(),
                        prev = layout.getPrev();
                    if ( prev ) {
                        layout.setActiveItem(prev);
                        cmp.fireEvent('cardChanged', prev, btn);
                    } else {
                        me.eventuallyDisableButton(btn);
                    }
                }
            },
            'uxNotification [cls*=validationResult] #card-next': {
                click: function(btn) {
                    var cmp = btn.up('[cls*=validationResult]'),
                        layout = cmp.getLayout(),
                        next = layout.getNext();
                    if ( next ) {
                        layout.setActiveItem(next);
                        cmp.fireEvent('cardChanged', next, btn);
                    } else {
                        me.eventuallyDisableButton(btn);
                    }
                }
            },
            'uxNotification [cls*=validationResult] [cls*=goToElement]': {
                click: function(btn) {
                    me.localizeElement();
                }
            },
            'uxNotification [cls*=validationResult] #moreInfo': {
                toggle: function(btn, pressed) {
                    me.setMoreInfoVisible(pressed);
                }
            },
            'main': {
                tabchange: function(panel, newCard, oldCard) {
                    if ( this.getValidationResult() ) {
                        me.localizeElement();

                        // If we're moving to or from the AKN preview tab, swap all 
                        // technical/simple messsages in errors.
                        if (newCard.xtype == "aknPreviewMainTab" || oldCard.xtype == "aknPreviewMainTab") {
                            var cmps = me.getValidationResult().query('[cls*=goToElement]');
                            cmps.forEach(function (cmp) {
                                var mainCmp = cmp.down('[cls*=errorsInfo]'),
                                    secCmp = cmp.down('[cls*=moreInfoPanel]');
                                // There seems to be no other way to swap the clean html...
                                mainCmp.swapped = !mainCmp.swapped;
                                if (mainCmp.swapped) {
                                    mainCmp.update(secCmp.initialConfig.html);
                                    secCmp.update(mainCmp.initialConfig.html);
                                } else {
                                    mainCmp.update(mainCmp.initialConfig.html);
                                    secCmp.update(secCmp.initialConfig.html);
                                }
                            });
                        }
                    }
                }
            }
        });
    }
});
