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

Ext.define('LIME.controller.NotesManagerController', {
    extend : 'Ext.app.Controller',

    config : {
        pluginName : "notesManager",
        authorialNoteClass : 'authorialNote',
        changePosAttr: 'chposid',
        changePosTargetAttr: 'chpos_id',
        refToAttribute: 'refto',
        notesContainerCls: 'notesContainer'
    },

    processNotes : function(editorBody) {
        var me = this, 
            athNotes = editorBody.querySelectorAll("*[class~='"+me.getAuthorialNoteClass()+"']"); 
        Ext.each(athNotes, function(element) {
            me.processNote(element, editorBody);
        }, me);  
    },
    
    getNotesContainer: function(editorBody) {
        var notesContainer = editorBody.querySelector("."+this.getNotesContainerCls()),
            docNode = editorBody.querySelector("."+DocProperties.documentBaseClass);
        if(!notesContainer && docNode) {
            notesContainer = Ext.DomHelper.createDom({
                tag : 'div',
                cls: this.getNotesContainerCls()
            });
            docNode.appendChild(notesContainer);
        }
        
        return notesContainer;
    },
    
    
    setNotePosition: function(note, refNode, editorBody) {
        var me = this, languageController = me.getController("Language"), 
            placement = languageController.nodeGetLanguageAttribute(note, "placement"), 
            allRefs = Array.prototype.slice.call(editorBody.querySelectorAll("*["+LoadPlugin.getRefToAttribute()+"]")),
            notesContainer, changed = false, refIndex, siblingNote, refSibling, refSiblingIndex;

        if (placement.value == "bottom" && note.parentNode && 
                    (!note.parentNode.getAttribute("class") || 
                        note.parentNode.getAttribute("class").indexOf(me.getNotesContainerCls()) == -1)) {
            notesContainer = me.getNotesContainer(editorBody);
            if(!notesContainer.childNodes.length) {
                notesContainer.appendChild(note);    
            } else {
                // Insert the note in order
                refIndex = allRefs.indexOf(refNode);
                for(var i = 0; i < notesContainer.childNodes.length; i++) {
                    siblingNote = notesContainer.childNodes[i];
                    refSibling = allRefs.filter(function(el) { 
                        return el.getAttribute(LoadPlugin.getRefToAttribute()) == siblingNote.getAttribute(LoadPlugin.getNoteTmpId());
                    })[0];
                    if(refSibling) {
                        refSiblingIndex = allRefs.indexOf(refSibling);
                        if(refSiblingIndex > refIndex) {
                            break;
                        }
                    }
                }
                if(siblingNote && refSiblingIndex > refIndex) {
                    notesContainer.insertBefore(note, siblingNote);
                } else {
                    notesContainer.appendChild(note);
                }
            }
            changed = true;
        } else if (placement.value == "inline" && note.parentNode && 
                (note.parentNode.getAttribute("class") && 
                    note.parentNode.getAttribute("class").indexOf(me.getNotesContainerCls()) != -1)) {
            if (refNode.nextSibling) {
                refNode.parentNode.insertBefore(note, refNode.nextSibling);
            } else {
                refNode.parentNode.appendChild(note);
            }
            changed = true;
        }
        return changed;
    },

    
    processNote: function(node, editorBody) {
        var me = this, parent = node.parentNode, app = me.application,
            languageController = me.getController("Language"),
            elId, tmpElement,  link, tmpExtEl,
            marker = languageController.nodeGetLanguageAttribute(node, "marker"),
            placement = languageController.nodeGetLanguageAttribute(node, "placement"),
            supLinkTemplate = new Ext.Template('<sup><a class="linker" href="#">{markerNumber}</a></sup>'),
            notTmpId = node.getAttribute(LoadPlugin.getNoteTmpId()),
            tmpRef = editorBody.querySelector("*["+LoadPlugin.getRefToAttribute()+"="+notTmpId+"]"),
            allRefs = Array.prototype.slice.call(editorBody.querySelectorAll("*["+LoadPlugin.getRefToAttribute()+"]")),
            clickLinker = function() {
                var marker = this.getAttribute(me.getRefToAttribute()),
                    note;
                if (marker) {
                    note = editorBody.querySelector("*["+LoadPlugin.getNoteTmpId()+"="+marker+"]");
                    if(note) {
                        app.fireEvent('nodeFocusedExternally', note, {
                            select : true,
                            scroll : true,
                            click : true
                        });    
                    }
                }  
            };
        if (tmpRef) {
            elId = allRefs.indexOf(tmpRef);
            elId = (elId != -1) ? elId+1 : "note";
            marker.value = marker.value || elId;
            placement.value = placement.value || "bottom";
            
            if(!tmpRef.querySelector('a')) {
                tmpElement = Ext.DomHelper.insertHtml("afterBegin", tmpRef, supLinkTemplate.apply({
                    'markerNumber' : marker.value
                }));
                tmpElement.querySelector('a').setAttribute(me.getRefToAttribute(), notTmpId);
                tmpElement.querySelector('a').onclick = clickLinker;    
            }
            
            node.setAttribute(marker.name, marker.value);
            node.setAttribute(placement.name, placement.value);
            me.setNotePosition(node, tmpRef, editorBody);
        }
    },
    
    updateNote: function(node, editorBody) {
        var me = this, languageController = me.getController("Language"),
            marker = languageController.nodeGetLanguageAttribute(node, "marker"),
            eId = node.getAttribute(LoadPlugin.getNoteTmpId()),
            ref = editorBody.querySelector("*["+LoadPlugin.getRefToAttribute()+"="+eId+"]"),
            linker, result = {marker: false, placement: false};
        if(eId && ref && marker && marker.value) {
            linker = ref.querySelector('a');
            if(marker.value.trim() !=  DomUtils.getTextOfNode(linker).trim()) {
                result.marker = true;
                linker.replaceChild(editorBody.ownerDocument.createTextNode(marker.value), linker.firstChild);  
            }
            result.placement = me.setNotePosition(node, ref, editorBody);
        }
        return result;
    },

    beforeProcessNotes: function(config) {
        this.processNotes(this.getController("Editor").getBody());
    },
    
    nodeChangedAttributes: function(node) {
        if(node.getAttribute("class").indexOf(this.getAuthorialNoteClass())!=-1) {
            var result = this.updateNote(node, this.getController("Editor").getBody());
            if(result.placement) {
                this.application.fireEvent('nodeFocusedExternally', node, {
                    select : true,
                    scroll : true,
                    click : true
                }); 
            }
        }
    },

    init : function() {
        var me = this;
        //Listening progress events
        me.application.on(Statics.eventsNames.afterLoad, me.beforeProcessNotes, me);
        me.application.on(Statics.eventsNames.nodeAttributesChanged, me.nodeChangedAttributes, me);
    }
});
