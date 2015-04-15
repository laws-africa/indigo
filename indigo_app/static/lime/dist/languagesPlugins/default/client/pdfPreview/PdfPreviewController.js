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

Ext.define('LIME.controller.PdfPreviewController', {
    extend : 'Ext.app.Controller',
    
    views: ["LIME.ux.pdfPreview.PdfPreviewMainTab"],

    refs : [{
        selector : 'appViewport',
        ref : 'appViewport'
    }, {
        selector: 'pdfPreviewMainTab',
        ref: 'pdf'
    }],

    config : {
        pluginName : "pdfPreview"
    },
    
    initPdf: function() {
        var me = this, pdfTab = me.getPdf(), editor = me.getController("Editor"),
            html = editor.getDocHtml(), styleSheet,
            iframePlugin  = pdfTab.getIframePlugin(), stylesheets;
        
        iframePlugin.setRawSrc(" ", function(iframeDoc) {
            iframeDoc = iframePlugin.getIfameDoc();
            if(iframeDoc) {
                iframeDoc.open();
                iframeDoc.write(html);
                iframeDoc.close();
            }
    
            stylesheets = iframeDoc.styleSheets;
            for(var i = 0; i < iframeDoc.styleSheets.length; i++) {
                styleSheet = iframeDoc.styleSheets.item(i);
                try {
                    me.processStyleSheet(iframeDoc, styleSheet);    
                } catch(e) {}
            }
            html = DomUtils.serializeToString(iframeDoc);
            me.callPdfService(html);
        });
        
    },
    
    applyCssRule: function(node, index, nodeList, cssText) {
        var previousStyle = node.getAttribute("style") || "";
        node.setAttribute("style", previousStyle+cssText);
    },
    
    processStyleSheet: function(doc, styleSheet) {
        var me = this, rule, nodes, cssText;
        for (var i = 0; i < styleSheet.cssRules.length; i++) {
            rule = styleSheet.cssRules.item(i);
            nodes = doc.querySelectorAll(rule.selectorText);
            cssText = (rule.style && rule.style.cssText) ? rule.style.cssText : 
                      rule.cssText.replace(/^[^{]*{/g, "").replace(/}/g, "").trim();
            if(nodes.length) {
                Ext.each(nodes, Ext.bind(me.applyCssRule, me, [cssText], true));
            }
        }
    },
    
    callPdfService: function(html) {
        var me = this, pdfTab = me.getPdf(), viewport = me.getAppViewport();
        
        viewport.setLoading(true);
        Ext.Ajax.request({
            // the url of the web service
            url : Utilities.getAjaxUrl(),
            
            // set the POST method
            method : 'POST',

            // send the content in html format
            params : {
                requestedService: Statics.services.htmlToPdf,
                source: html
            },
            // the scope of the ajax request
            scope : me,

            // if the translation was is performed
            success : function(result, request) {
                var jsonData = Ext.decode(result.responseText, true);
                
                if(!jsonData) {
                    jsonData = {status: "Error", description: "Reading results error"};
                }
                //If there is an url set it in the panel otherwise show the error
                if (jsonData.absolutePathPDF) {
                    pdfTab.setPdf(jsonData.absolutePathPDF);
                } else {
                    Ext.MessageBox.alert(Ext.String.capitalize(jsonData.status), jsonData.description);
                }
                viewport.setLoading(false);
            },
            failure: function() {
                viewport.setLoading(false);
            }
        });  
    },
    
    
    init : function() {
        var me = this;
        this.control({
            'pdfPreviewMainTab' : {
                activate : me.initPdf
            }
        });
    }
});
