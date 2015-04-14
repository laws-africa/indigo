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

Ext.define('LIME.controller.AknWidgetManagerController', {
    extend : 'Ext.app.Controller',

    refs : [{
        selector: 'markedElementWidget',
        ref: 'markedElementWidget'
    }],

    config : {
        pluginName : "widgetManager"
    },
    
    init : function() {
        var me = this;
        this.control({
            'markedElementWidget field' : {
                change : function(cmp) {
                    var widget = cmp.up("markedElementWidget"),
                        element = DocProperties.getMarkedElement(widget.id);
                    
                    if (element && element.button) {
                        switch (element.button.name) {
                            case 'ref':
                                me.onRefFieldChange(cmp, widget);
                                break;
                        }
                    }
                }
            }
        });
    },

    onRemoveController: function() {
        var me = this;
        me.application.removeListener(Statics.eventsNames.nodeAttributesChanged, me.onNodeAttributeChange, me);
    },
    
    onInitPlugin: function() {
        var me = this;
        me.application.on(Statics.eventsNames.nodeAttributesChanged, me.onNodeAttributeChange, me);
    },

    onRefFieldChange: function(cmp, widget) {
        var editor = this.getController('Editor');
        if (cmp.origName == 'type') {
            var value = cmp.getValue(),
                artNum = widget.down('[name=artnum]');
            if ( value == 'internal' ) {
                widget.query('field').filter(function(field) {
                    return field.name != 'type';
                }).forEach(function(field) {
                    field.disable();
                });
                artNum.hide();
                widget.add(this.createNumsCombo(artNum));
            } else {
                widget.query('field').forEach(function(field) {
                    field.enable();
                });
                artNum.show();
                var comboArtNum = widget.down('combo[name=artnum]');
                if ( comboArtNum ) {
                    comboArtNum.destroy();
                }
            }
        }
    },

    createNumsCombo: function(field) {
        return Ext.widget('combo', {
            emptyText: field.emptyText,
            name: field.name,
            origName: field.origName,
            displayField: 'text',
            store : Ext.create('Ext.data.Store', {
                    fields: ["text", "id"],
                    data: this.getNumsValues()
            }),
            queryMode: 'local'
        });
    },

    getNumsValues: function() {
        var editor = this.getController('Editor'),
            body = editor.getBody();

        return Ext.Array.toArray(body.querySelectorAll('.num')).filter(function(node) {
            var quotedParent = Ext.fly(node).parent('.quotedStructure') || Ext.fly(node).parent('.quotedText');
            return (quotedParent) ? false : true;
        }).map(function(node) {
            return {
                text: node.textContent,
                id: node.getAttribute(DomUtils.elementIdAttribute)
            };
        });
    },

    onNodeAttributeChange: function(node) {
        var config = DomUtils.getButtonByElement(node);
        if ( config && config.name == 'ref' ) {
            var attName = Language.getAttributePrefix()+'href',
                href = node.getAttribute(attName);
            
            if ( href ) {
                var artNum = href.substring(href.lastIndexOf('#')+1);
                if ( artNum.trim() ) {
                    var nums = this.getNumsValues();
                    var obj = nums.filter(function(obj) {
                        return obj.text = artNum;
                    })[0];
                    var numNode = (obj) ? DocProperties.getMarkedElement(obj.id) : null;
                    var parentId = (numNode) ? numNode.htmlElement.parentNode.getAttribute(DomUtils.elementIdAttribute) : null;
                    href = (parentId) ? href.replace(artNum, parentId) : href;
                }
                href = href.replace(/(\/\/)+/, '/').replace('\/#','#').replace('##', '#');
                node.setAttribute(attName, href);
            }

        }
    }
});
