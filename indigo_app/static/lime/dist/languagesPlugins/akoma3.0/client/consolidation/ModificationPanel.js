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
 * must include the  acknowledgment: "This product includes
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
 * TORT OR OTHERWISEfollowing, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */


Ext.define('LIME.ux.consolidation.ModificationPanel', {
    extend: 'Ext.panel.Panel',
    alias: 'widget.modification',

    initComponent: function () {
        this.callParent();
        this.store =  Ext.create('Ext.data.Store', {
            model: 'LIME.ux.consolidation.ModificationModel',
            pageSize: 1,
            data: this.modifications,
            proxy: {
                type: 'memory',
                reader: {
                    type: 'json',
                    totalProperty: this.modifications.length
                }
            },

            // Get current modification model instance
            getCurrent: function () {
                return this.getAt(this.currentPage-1);
            }
        });

        var update = (function () {
            var modification = this.store.getCurrent();

            var pagingtoolbar = this.down('pagingtoolbar'),
                descriptionLabel = pagingtoolbar.getComponent('modificationDescription'),
                applyButton = pagingtoolbar.getComponent('applyButton');

            var msg = '<b>' + modification.get('type') + '</b> at <i>' + modification.getVerboseDescription() + '</i>';
            descriptionLabel.setText(msg, false);

            console.log('executed', modification.get('executed'));
            if (modification.get('executed')) {
                applyButton.disable();
                pagingtoolbar.getComponent('inputItem').setFieldStyle('background-color: #7a7; background-image: none;');
            } else {
                applyButton.enable();
                pagingtoolbar.getComponent('inputItem').setFieldStyle('background-color: rgb(250, 252, 192); background-image: none;');
            }
        }).bind(this);

        this.store.on('datachanged', update);
        this.on('afterrender', update);

        this.down('pagingtoolbar').bindStore(this.store);
        this.down('progressbar').setProgress(0, this.modifications.length);
    },


    layout: { type: 'hbox' },

    items: [{
        xtype: 'progressbar',
        flex: 1000,
        template: new Ext.Template('Executed {0} of {1}. <a>(Click for report)</a>'),
        
        setProgress: function (completed, total) {
            this.updateProgress(completed/total);
            this.updateText(this.template.apply([completed, total]), false);
        },

        initEvents: function () {
            this.superclass.initEvents.call(this);
            this.el.on('click', function () {
                this.fireEvent('displayReport');
            }.bind(this));
        }
    }],

    dockedItems: [{
        xtype: 'pagingtoolbar',
        dock: 'top',
        displayInfo: true,
        border: 0,
        beforePageText: Locale.getString('Pagination_beforePageText', 'consolidation'),
        displayMsg: '',
        listeners: {
            'afterrender': function (e) {
                this.el.down('.x-tbar-loading').hide();
            }
        },

        items: [{
            xtype: 'label',
            itemId: 'modificationDescription',
            flex: 1000,
            style: {
                marginLeft: '80px',
                fontSize: '18px',
                padding: '7px',
                color: 'rgb(4, 70, 140)'
            },

            listeners: {
                'afterrender': function (e) {
                    var me = this;
                    e.el.on('click', function () {
                        console.log('click');
                        me.up('pagingtoolbar').doRefresh();
                    });
                }
            },

        }, {
            xtype: 'button',
            itemId: 'applyButton',
            style: {
                backgroundImage: 'linear-gradient(to bottom, #4ba614, #008c00)',
                border: '1px solid #008c00',
                boxShadow: '2px 2px 2px #666',
            },
            text: '<span style="color:black">Apply this modification</span>'
        }]
    }]

});
