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
Ext.define('LIME.ux.Language', {
    /* Since this is merely a utility class define it as a singleton (static members by default) */
    singleton : true,
    alternateClassName : 'Language',

    name : 'Akoma ntoso',

    config : {
        elementIdAttribute: "id",
        attributePrefix: "akn_",
        metadataStructure : {},
        abbreviations : {
            alinea : "al",
            article : "art",
            attachment : "att",
            blockList : "list",
            chapter : "chp",
            citation : "cit",
            citations : "cits",
            clause : "cl",
            component : "cmp",
            components : "cmpnts",
            componentRef : "cref",
            debateSection : "dbsect",
            division : "dvs",
            documentRef : "dref",
            eventRef : "eref",
            intro : "intro",
            list : "list",
            listIntroduction : "intro",
            listWrapUp : "wrap",
            paragraph : "para",
            quotedStructure : "qstr",
            quotedText : "qtext",
            recital : "rec",
            recitals : "recs",
            section : "sec",
            subchapter : "subchp",
            subclause : "subcl",
            subdivision : "subdvs",
            subparagraph : "subpara",
            subsection : "subsec",
            temporalGroup : "tmpg",
            wrapUp : "wrapup"
        },
        noPrefixElements : ["collectionBody", "body", "mainBody", "documentRef", "componentRef", "mod"],
        noIdElements: ["preface", "preamble", "body", "mainBody", "collectionBody"],
        noIdPatterns: ["block", "inline"],
        exceptIdElements: ["mod", "documentRef", "componentRef", "heading", "ins", "del"],
        documentContextElements: ["mod", "article"],
        noIdNumElements: ["components", "conclusions", "content", "heading"],
        prefixSeparator: "__",
        numSeparator: "_"
    },

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
    translateContent : function(content, markingLanguage, callbacks) {
        var params = {
            output : 'akn',
            markingLanguage : markingLanguage
        }, transformFile = Config.getLanguageTransformationFile("LIMEtoLanguage");

        XsltTransforms.transform(content, transformFile, params, callbacks.success, callbacks.failure);
    },

    needsElementId: function(elName, button) {
        var pattern = (button) ? button.pattern.pattern : null;

        return (elName && (this.getNoIdElements().indexOf(elName) == -1) && 
                ( ( !pattern || this.getNoIdPatterns().indexOf(pattern) == -1 ) ||
                ( this.getExceptIdElements().indexOf(elName) != -1 ) ) );
    },

    skipGeneratingId: function( node ) {
        return true;
    },

    /* Find elNum by counting the preceding elements with 
       in given the same name in the context.*/

    getElNum: function(element, elName, context) {
        var elNum = false,
            num = Ext.fly(element).down('.num', true);

        if ( num && (num.parentNode == element || Ext.fly(num.parentNode).is('.content')) ) {
            var text = (num) ? num.textContent : "",
                numVal = text.match(/(?:[\u00C0-\u1FFF\u2C00-\uD7FF\w]+\W*\s+)*(\w+\s*\w*)/),
                romanChecker = new RegExp(/M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})/);

            elNum = (numVal && numVal.length) ? numVal[numVal.length-1] : false;
            var romanNumer = (elNum) ? elNum.match(romanChecker) : false;
            elNum = (elNum && (!romanNumer || !romanNumer[0].length ) ) ? elNum.toLowerCase() : elNum;
            elNum = elNum.replace(/\s/g,'');
        }

        if ( !elNum ) {
            elNum = 1;
            var siblings = context.querySelectorAll("*[class~="+elName+"]");
            if(siblings.length) {
                var elIndexInParent = Array.prototype.indexOf.call(siblings, element);
                elNum = (elIndexInParent!=-1) ? elIndexInParent+1 : elNum;    
            }
        }
        return elNum;
    },

    getMarkingIdParentPart: function(elName, markedParent, documentContext) {
        var markingId = '',
            attributeName = Language.getAttributePrefix() + DomUtils.langElementIdAttribute,
            parentName = (markedParent) ? DomUtils.getNameByNode(markedParent) : false,
            cmpParent = (documentContext) ? documentContext.parent('.component', true) : false,
            cmpPrefix = (cmpParent) ? cmpParent.getAttribute(attributeName)+this.getPrefixSeparator() : "";

        if( markedParent && this.getNoPrefixElements().indexOf(parentName) == -1 
                         && this.getNoPrefixElements().indexOf(elName) == -1 ) {

            markingId += markedParent.getAttribute(attributeName) ? markedParent.getAttribute(attributeName) 
                                                        : "";
            markingId += (!markingId) ? this.getMarkingIdParentPart(parentName, DomUtils.getFirstMarkedAncestor(markedParent.parentNode)) 
            										: this.getPrefixSeparator();
        }

        if ( cmpPrefix && !Ext.String.startsWith(markingId,cmpPrefix) ) {
            markingId = cmpPrefix+markingId;
        }
        return markingId;
    },

    getLanguageMarkingId : function(element, langPrefix, root, counters, enforce) {
        var me = this, markingId = "",
            button = DomUtils.getButtonByElement(element),
            elName = (button) ? button.name : DomUtils.getNameByNode(element);

        if ( me.skipGeneratingId(root) ) return markingId;
        try {
            if ( enforce || me.needsElementId(elName, button) ) {
                var markedParent = DomUtils.getFirstMarkedAncestor(element.parentNode),
                    documentContext = Ext.fly(element).parent('.document'),
                    
                markingId = me.getMarkingIdParentPart(elName, markedParent, documentContext);

                var context = markedParent || root;
                var alternativeContext = Ext.fly(element).parent('.collectionBody', true);
                context = (alternativeContext) ? alternativeContext : context;

                if ( me.getDocumentContextElements().indexOf(elName) != -1 ) {
                    context = Ext.fly(element).parent('.mod', true) || documentContext.dom;
                } else if ( elName != 'content' && Ext.fly(element).findParent( '.content', 2, true ) ) {
                    markingId+='content'+me.getPrefixSeparator();
                }

                var elNum = me.getElNum(element, elName, context);

                var elementRef = (me.getAbbreviations()[elName]) ? (me.getAbbreviations()[elName]) : elName;
                markingId += elementRef;
                if ( me.getNoIdNumElements().indexOf(elName) == -1 ) {
                    markingId += me.getNumSeparator()+elNum;
                }

            }
        } catch(e) {
            console.log(e, elName);
        }
        return markingId;
    },

    onNodeChange : function(node, deep) {
        var me = this, fly = Ext.fly(node);
        if (!node) return;
        
        if ( deep === false ) {
            DomUtils.setNodeInfoAttr(node, 'hcontainer', " ({data})");
        } else if ( fly && fly.is('.inline')) {
            me.onNodeChange(fly.parent('.hcontainer', true), false);
        } else {
            Ext.each(Ext.Array.push(Ext.Array.toArray(node.querySelectorAll('.hcontainer')), node), function(node) {
                me.onNodeChange(node, false);
            });
        }
    }
});
