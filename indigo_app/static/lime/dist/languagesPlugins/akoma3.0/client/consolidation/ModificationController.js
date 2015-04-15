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

Ext.define('LIME.controller.ModificationController', {
    extend: 'Ext.app.Controller',
    views: [
        'LIME.ux.consolidation.ModificationPanel',
        'modal.newSavefile.Main'
    ],
    
    refs: [
        { ref: 'viewport', selector: 'appViewport' }, 
        { ref: 'mainToolbar', selector: 'mainToolbar' },
        { ref: 'panel', selector: 'modification' },
        { ref: 'pager', selector: 'modification pagingtoolbar' },
        { ref: 'progressbar', selector: 'modification progressbar' }
    ],
    
    modifications: [],
    
    init: function () {
        var me = this;
        this.control({
            'modification #applyButton': {
                'click': function () {
                    me.showConfirmationDialog(function () {
                        var modification = me.getPanel().store.getCurrent();
                        me.execute(modification);
                        modification.set('executed', true);
                        me.getPager().moveNext();
                        me.getPanel().store.reload();
                        var executedCounter = me.modifications.filter(function (mod) {
                            return mod.get('executed');
                        }).length;
                        me.getProgressbar().setProgress(executedCounter, me.modifications.length);


                        if(executedCounter == me.modifications.length)
                            me.application.fireEvent(Statics.eventsNames.showNotification, {
                                title: Locale.getString('successMessage', 'consolidation'),
                                content: me.executedCounter + ' modifications applied.',
                                width: 300,
                                status: true
                            });
                        else
                            me.displayModification(modification);

                    })
                }
            },
            'modification progressbar': {
                'displayReport': function () {
                    Ext.create('LIME.ux.consolidation.ReportWindow', {
                        modifications: me.modifications
                    }).show();
                }
            }
        });
    },

    // Main entry point: cycle all modifications and apply
    // them if user wants to.
    consolidate: function (modifications, modifyingDom, modifiedDom) {
        var me = this;
        this.modifyingDom = modifyingDom;
        this.modifiedDom = modifiedDom;

        this.modifications = Ext.toArray(modifications)
            .map(this.createModObject.bind(this))
            .map(function (modification) {
                return  Ext.create('LIME.ux.consolidation.ModificationModel', {
                    type: modification.type,
                    destHref: modification.destinationHref,
                    executed: false,
                    source: modification.source,
                    new: modification.new,
                    destinations: modification.destinations
                });
            });

        var toolbarPanel = this.getMainToolbar().up('panel');

        this.toolbar = toolbarPanel.addDocked({
            xtype: 'modification',
            dock: 'bottom',
            modifications: this.modifications
        })[0];

        Ext.defer(function () {
            function update () {
                me.displayModification(me.getPanel().store.getCurrent());
            };
            me.getPanel().store.on('datachanged', update);
            update();
        }, 1000);

        // Viva i barbatrucchi, buon natale!
        this.getViewport().addCls('consolidationMode');
    },

    createModObject: function(node) {
        var obj = {
            type: node.getAttribute('type')
        };

        var source = node.querySelector('[class=source]');
        var sourceHref = (source) ? source.getAttribute(Language.attributePrefix+'href') : false;
        sourceHref = (sourceHref) ? sourceHref.replace('#', '') : false;

        if ( sourceHref ) {
            var modNode = this.modifyingDom.querySelector('['+Language.attributePrefix+'eId'+'='+sourceHref+'], ['+Language.attributePrefix+'wId'+'='+sourceHref+']');
            if ( modNode ) {
                obj.source = modNode;
            }
        }

        var newNode = node.querySelector('[class=new]');
        var newHref = (newNode) ? newNode.getAttribute(Language.attributePrefix+'href') : false;
        newHref = (newHref) ? newHref.replace('#', '') : false;
        if ( newHref ) {
            newNode = this.modifyingDom.querySelector('['+Language.attributePrefix+'eId'+'='+newHref+']');
            if ( newNode ) {
                obj.new = newNode;
                var forRef = newNode.getAttribute(Language.attributePrefix+'for');
                if ( forRef ) {
                    console.log('Find destinations forRef', forRef);
                    this.findDestinations(obj, forRef.replace('#', ''));
                }
                if ( !obj.source ) {
                    obj.source = Ext.fly(newNode).parent('.mod', true);
                }
            }
        }

        if ( Ext.isEmpty(obj.destinations) && obj.source ) {
            var refNode = obj.source.querySelector('.ref, .rref');
            console.log('Find destinations ultimo ramo', refNode);
            this.findDestinations(obj, false, refNode);
        }
        return obj;
    },

    findDestinations: function(output, refId, refNode) {
        var me = this;
        output.destinations = [];
        refNode = refNode || this.modifyingDom.querySelector('['+Language.attributePrefix+'eId'+'='+refId+']');
        console.log('WTF', refNode);
        if ( refNode ) {
            var elementName = DomUtils.getNameByNode(refNode);
            switch( elementName ) {
                case 'ref':
                    var from = me.getIdFromHref(refNode.getAttribute(Language.attributePrefix+'href'));
                    var fromNode = ( from ) ? me.modifiedDom.querySelector('['+Language.attributePrefix+'eId'+'*='+from+']') : false;
                    output.destinationHref = from;
                    console.log('destinationHref', from);
                    if ( fromNode ) {
                        output.destinations = [fromNode];
                    }
                break;
                case 'rref':
                    var from = me.getIdFromHref(refNode.getAttribute(Language.attributePrefix+'from'));
                    var upTo = me.getIdFromHref(refNode.getAttribute(Language.attributePrefix+'upTo'));
                    var fromNode = ( from ) ? me.modifiedDom.querySelector('['+Language.attributePrefix+'eId'+'*='+from+']') : false;
                    var upToNode = ( upTo ) ? me.modifiedDom.querySelector('['+Language.attributePrefix+'eId'+'*='+upTo+']') : false;
                    output.destinationHref = from;
                    console.log('destinationHref', from);
                    if ( fromNode && upToNode ) {
                        output.destinations = DomUtils.getSiblings(fromNode, upToNode, 'div');;
                    }
                break;
            }
        }
    },

    getIdFromHref: function(href) {
        if ( href ) {
            return href.substring(href.lastIndexOf('#')+1);
        }
    },

    // Inform user consolidation completed.
    success: function () {
        Ext.widget('newSavefileMain').show();

        this.clearHighlight();
        this.getMainToolbar().up('panel').removeDocked(this.toolbar);
        this.getViewport().removeCls('consolidationMode');
    },

    // Show modification in editor.
    displayModification: function (modification) {
        console.log('displayModification', modification.get('source'));
        this.clearHighlight();
        modification.get('source').scrollIntoView();
        modification.get('source').setAttribute('highlighted', 'true');

        try {
            modification.get('destinations')[0].scrollIntoView();
        } catch (e) {
            Ext.log('destination not found');
        }
        Ext.each(modification.get('destinations'), function (el) {
            el.setAttribute('highlighted', 'true');
        });
    },

    clearHighlight: function () {
        var elements = this.modifyingDom.querySelectorAll('*[highlighted=true]');
        for (var i = 0; i < elements.length; i++)
            elements[i].removeAttribute('highlighted');
        var elements = this.modifiedDom.querySelectorAll('*[highlighted=true]');
        for (var i = 0; i < elements.length; i++)
            elements[i].removeAttribute('highlighted');
    },

    // Ask user if he really wants to apply a modification.
    // Execute callback on affermative answer.
    showConfirmationDialog: function (callback) {
        Ext.Msg.show({
            title: Locale.getString('dialogTitle', 'consolidation'), 
            msg: Locale.getString('dialogQuestion', 'consolidation'),
            buttons: Ext.Msg.YESNOCANCEL,
            fn: function(btn) {
                if (btn == 'yes') {
                    callback();
                }
            }
        });
    },

    // Apply modification
    execute: function (modification) {
        Ext.each(modification.get('destinations'), function(destNode) {
            var destId = destNode.getAttribute(Language.attributePrefix+'eId');
            var newNode = modification.get('new').querySelector('['+Language.attributePrefix+'eId'+'*='+destId+']');
            if ( newNode ) {
                var clonedNode = newNode.cloneNode(true);
                destNode.parentNode.replaceChild(clonedNode, destNode);
                var wrapUp = Ext.fly(newNode).next('.wrapUp', true);
                // If wrapUp is the next div
                if ( wrapUp && DomUtils.getSiblings(newNode, wrapUp, 'div').length == 2 ) {
                    DomUtils.insertAfter(wrapUp.cloneNode(true), clonedNode);
                }
            } else {
                destNode.parentNode.removeChild(destNode);
            }
        });
    }
});
