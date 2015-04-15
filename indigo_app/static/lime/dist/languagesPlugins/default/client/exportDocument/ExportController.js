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

Ext.define('LIME.controller.ExportController', {
    extend : 'Ext.app.Controller',

    refs : [{
        ref : 'downloadManager',
        selector : 'downloadManager'
    }],
    
    config : {
        pluginName : "exportDocument"
    },
    
    initMenu : function() {
        var me = this;
        me.addExportItem();
    },
    
    addExportItem: function() {
        var me = this;
        menu = {
            text : Locale.getString("exportDocument", me.getPluginName()),
            icon : 'resources/images/icons/export-icon.png',
            name : 'exportAs',
            id : 'exportMenu',
            hideOnClick: false,
            menu : {
                plain : true,
                items : [{
                    text : Locale.getString("exportXml", me.getPluginName()),
                    tooltip : Locale.getString("exportXmlTooltip", me.getPluginName()),
                    icon : 'resources/images/icons/file-xml.png',
                    name : 'exportXmlButton'
                }, {
                    text : Locale.getString("exportHtml", me.getPluginName()),
                    tooltip : Locale.getString("exportHtmlTooltip", me.getPluginName()),
                    icon : 'resources/images/icons/html.png',
                    name : 'exportHtmlButton'
                }, {
                    text : Locale.getString("exportPdf", me.getPluginName()),
                    tooltip : Locale.getString("exportPdfTooltip", me.getPluginName()),
                    icon : 'resources/images/icons/file-pdf.png',
                    name : 'exportPdfButton'
                }, {
                    text : Locale.getString("exportEbook", me.getPluginName()),
                    tooltip : Locale.getString("exportEbookTooltip", me.getPluginName()),
                    icon : 'resources/images/icons/file-epub.png',
                    name : 'exportEbookButton'
                }]
            }
        };
        me.application.fireEvent("addMenuItem", me, {
            menu : "fileMenuButton"
        }, menu);
    },
    
    /**
     * This function exports the document using the download manager
     * @param {String} url The url of download service
     * @param {Object} params Params to pass to the download service
     */
    exportDocument: function(url, params) {
        var downloadManager = this.getDownloadManager();
        // Set a callback function to translateContent
        this.application.fireEvent(Statics.eventsNames.translateRequest, function(xml) {
            var parameters = Ext.Object.merge(params, {source: xml});
            downloadManager.fireEvent(downloadManager.eventActivate, url, parameters);
        }, {complete: true});
    },
    
    onInitPlugin: function() {
        var me = this;
        me.initMenu();
    },
            
    init : function() {
        var me = this;

        this.control({
            'menu [name=exportXmlButton]': {
                click: function() {
                    me.exportDocument(Utilities.getAjaxUrl(), {
                        requestedService: Statics.services.xmlExport
                    });
                }
            },
            'menu [name=exportHtmlButton]': {
                click: function() {
                    me.exportDocument(Utilities.getAjaxUrl(), {
                        requestedService: Statics.services.htmlExport
                    });
                }
            },
            'menu [name=exportPdfButton]': {
                click: function() {
                    var downloadManager = me.getDownloadManager(),
                        editor = me.getController("Editor"),
                        parameters = {
                            requestedService: Statics.services.pdfExport,
                            source: editor.getDocHtml()
                        };
                    downloadManager.fireEvent(downloadManager.eventActivate, Utilities.getAjaxUrl(), parameters);
                }
            },
            'menu [name=exportEbookButton]': {
                click: function() {
                    //TODO: set the right title of document
                    me.exportDocument(Utilities.getAjaxUrl(), {
                        requestedService: Statics.services.aknToEpub,
                        lang: DocProperties.getLang(),
                        title: 'LIME ebook'
                    });
                }
            }
        });
    }
});
