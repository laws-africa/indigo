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
 * Language dependent utilities
 */
Ext.define('WAWE.ux.Language', {
    /* Since this is merely a utility class define it as a singleton (static members by default) */
    singleton : true,
    alternateClassName : 'Language',
    
    name: 'Akoma ntoso',
    
    /**
     * Translate the content based on an external web service (called by 
     * an ajax request) which uses a XSLT stylesheet.
     * If the ajax request is successful the success callback is called.
     * Note that this function doesn't return anything since it asynchronously
     * call callback functions.
     * 
     * @param {String} content The content to translate
     * @param {Object} callbacks Functions to call after translating 
     */
    translateContent : function(content, callbacks) {

        //Calling the translate service
        Ext.Ajax.request({
            // the url of the web service
            url : Utilities.getAjaxUrl(),
            method : 'POST',
            // send the content in XML format
            params : {
                requestedService : Statics.services.xsltTrasform,
                output : 'akn',
                input : content
            },
            scope : this,
            // if the translation was performed
            success : function(result, request) {
                //TODO: fix this
                var xml = result.responseText.replace('<akomaNtoso>', '<akomaNtoso xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.akomantoso.org/2.0 ./akomantoso20.xsd" xmlns="http://www.akomantoso.org/2.0">');
                if (Ext.isFunction(callbacks.success)) {
                    callbacks.success(xml);
                }
            },
            failure: callbacks.failure
        });
    }
    
});