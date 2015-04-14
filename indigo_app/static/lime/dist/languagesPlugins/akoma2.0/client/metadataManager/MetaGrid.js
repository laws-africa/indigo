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

Ext.define('LIME.ux.metadataManager.MetaGrid', {

    extend : 'Ext.grid.Panel',

	requires : ['Ext.grid.plugin.CellEditing'],
	
    alias : 'widget.metaGrid',
    
    config : {
        pluginName : "metadataManager",
        genericColumn: {
	        resizable : false,
	        hideable : false,
	        menuDisabled : true,
	        editor : {
	            selectOnFocus : true,
	            allowBlank : false
	        }
	    }
    },
    columns : [],
    plugins : [{
        ptype : "cellediting",
        pluginId : 'cellediting',
        clicksToEdit : 1
    }],
    tools : [{
        type : 'plusUri',
        tooltip : Locale.getString("addUri", "uriManager"),
        listeners : {
            afterrender : function(cmp) {
                this.up("metaGrid").setAddIcon(cmp);
            }
        }
    }],
    setAddIcon : function(cmp) {
        cmp.toolEl.removeCls("x-tool-plus");
        cmp.toolEl.setStyle("backgroundImage", 'url("resources/images/icons/add.png")');
    },
    initComponent: function() {
    	var me = this, templateColumn = me.getGenericColumn();
	    me.columns = [];
	    Ext.each(me.columnsNames, function(name) {
	        var column = Ext.merge(Ext.clone(templateColumn), {
                    text: Ext.String.capitalize(name.replace("akn_", "")),
                    dataIndex: name,
                    flex: 1
            });
	        if(me.customColumns && Ext.isArray(me.customColumns[name])) {
	            column.editor.xtype = "combo";
	            var store = Ext.create('Ext.data.Store', {
                    fields: ["type"],
                    data : me.customColumns[name].map(function(el) {return {"type": el};})
                });
                column.editor.store = store;
                column.editor.queryMode = 'local';
                column.editor.displayField = 'type';
                column.editor.valueField = 'type';
	        }
	        me.columns.push(column);    
	    	
	    });
	    
	    me.columns.push({
	        xtype : 'actioncolumn',
	        width : 30,
	        sortable : false,
	        menuDisabled : true,
	        items : [{
	            icon : 'resources/images/icons/delete.png',
	            tooltip : Locale.getString("removeComponent", "uriManager"),
	            scope : me,
	            handler : function(grid, rowIndex) {
	                grid.getStore().removeAt(rowIndex);
	            }
	        }]
	    });
	    
	    me.store.grid = me;
	    
    	me.callParent(arguments);
    }
});
