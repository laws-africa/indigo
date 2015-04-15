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

Ext.define('LIME.controller.ImportController', {
    extend : 'Ext.app.Controller',

    config : {
        pluginName : "importDocument"
    },

    initMenu : function() {
        var me = this;
        menu = {
            xtype : 'menuseparator',
            name : 'importSeparator'
        };
        me.application.fireEvent("addMenuItem", me, {
            menu : "fileMenuButton",
            after : "saveAsDocumentButton"
        }, menu);
        me.addImportItem();
    },

    addImportItem : function() {
        var me = this;
        menu = {
            text : Locale.getString("importDocument", me.getPluginName()),
            tooltip : Locale.getString("importDocumentTooltip", me.getPluginName()),
            icon : 'resources/images/icons/import-icon.png',
            name : 'importDocument'
        };
        me.application.fireEvent("addMenuItem", me, {
            menu : "fileMenuButton",
            after : "importSeparator"
        }, menu);
    },
    
    uploadFinished: function(content, request) {
        var app = this.application, docMLang, docLang;
        if(request.response && request.response[DocProperties.markingLanguageAttribute]) {
            docMLang = request.response[DocProperties.markingLanguageAttribute]; 
        }
        if(request.response && request.response[DocProperties.languageAttribute]) {
            docLang = request.response[DocProperties.languageAttribute] || "";
        }

        content = content.replace(/(<br\/>(<br\/>)?(\s*))+/g, '$1');

        // Upload the editor's content
        app.fireEvent(Statics.eventsNames.loadDocument, {
                        docText: content, 
                        docMarkingLanguage: docMLang,
                        docLang: docLang
        });
    },

    importDocument : function() {
        // Create a window with a form where the user can select a file
        var me = this, 
            transformFile = Config.getLanguageTransformationFile("languageToLIME", Config.getLanguage()),
            uploaderView = Ext.widget('uploader', {
                buttonSelectLabel : Locale.getString("selectDocument", me.getPluginName()),
                buttonSubmitLabel : Locale.getString("importDocument", me.getPluginName()),
                dragDropLabel : Locale.getString("selectDocumentExplanation", me.getPluginName()),
                title : Locale.getString("importDocument", me.getPluginName()),
                uploadCallback : me.uploadFinished,
                callbackScope: me,
                uploadUrl : Utilities.getAjaxUrl(),
                uploadParams : {
                    requestedService: Statics.services.fileToHtml,
                    transformFile: (transformFile) ? transformFile : ""
                }
            });
        uploaderView.show();
    },
    
    onInitPlugin : function() {
        var me = this;
        me.initMenu();
    },

    init : function() {
        var me = this;

        this.control({
            'menu [name=importDocument]' : {
                click : function() {
                    me.importDocument();
                }
            }
        });
    }
});
