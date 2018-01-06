(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // The SourceEditorView manages the interaction between
  // the model, the wrapping document editor view, and the source (xml) and
  // text editor components.
  Indigo.SourceEditorView = Backbone.View.extend({
    el: '#content-tab',
    events: {
      'click .text-editor-buttons .btn.save': 'saveTextEditor',
      'click .text-editor-buttons .btn.cancel': 'closeTextEditor',
      'click .btn.edit-text': 'fullEdit',
      'click .btn.edit-table': 'editTable',
      'click .quick-edit a': 'quickEdit',
    },

    initialize: function(options) {
      var self = this;

      this.parent = options.parent;
      this.name = 'source';
      this.grammar_fragments = {
        chapter: 'chapters',
        part: 'parts',
        section: 'sections',
        component: 'schedules',
        components: 'schedules_container',
      };
      this.quickEditable = '.akn-chapter, .akn-part, .akn-section, .akn-component, .akn-components';
      this.quickEditTemplate = $('<div class="quick-edit ig"><a href="#"><i class="fa fa-pencil"></i></a></div>');

      // setup renderer
      var htmlTransform = new XSLTProcessor();
      $.get('/static/xsl/act.xsl')
        .then(function(xml) {
          htmlTransform.importStylesheet(xml);
          htmlTransform.setParameter(null, 'resolverUrl', Indigo.resolverUrl);
          self.htmlTransform = htmlTransform;
        });

      // setup xml editor
      this.xmlEditor = ace.edit(this.$(".document-xml-editor .ace-editor")[0]);
      this.xmlEditor.setTheme("ace/theme/monokai");
      this.xmlEditor.getSession().setMode("ace/mode/xml");
      this.xmlEditor.setValue();
      this.xmlEditor.$blockScrolling = Infinity;
      this.onEditorChange = _.debounce(_.bind(this.xmlEditorChanged, this), 500);

      // setup text editor
      this.$textEditor = this.$('.document-text-editor');
      this.textEditor = ace.edit(this.$(".document-text-editor .ace-editor")[0]);
      this.textEditor.setTheme("ace/theme/xcode");
      this.textEditor.getSession().setMode("ace/mode/indigo");
      this.textEditor.setValue();
      this.textEditor.getSession().setUseWrapMode(true);
      this.textEditor.setShowPrintMargin(false);
      this.textEditor.$blockScrolling = Infinity;

      // setup table editor
      this.tableEditor = new Indigo.TableEditorView({parent: this, documentContent: this.parent.documentContent});
      this.tableEditor.on('start', this.tableEditStart, this);
      this.tableEditor.on('finish', this.tableEditFinish, this);

      var textTransform = new XSLTProcessor();
      $.get('/static/xsl/act_text.xsl')
        .then(function(xml) {
          textTransform.importStylesheet(xml);
          self.textTransform = textTransform;
        });

      // menu events
      this.$menu = $('.workspace-header .menu');
      this.$menu
        .on('click', '.edit-find a', _.bind(this.editFind, this))
        .on('click', '.edit-find-next a', _.bind(this.editFindNext, this))
        .on('click', '.edit-find-previous a', _.bind(this.editFindPrevious, this))
        .on('click', '.edit-find-replace a', _.bind(this.editFindReplace, this))
        .on('click', '.edit-insert-image a', _.bind(this.insertImage, this))
        .on('click', '.edit-insert-table a', _.bind(this.insertTable, this));
    },

    fullEdit: function(e) {
      e.preventDefault();
      this.editFragmentText(this.parent.fragment);
    },

    quickEdit: function(e) {
      var elemId = e.currentTarget.parentElement.parentElement.id,
          node = this.parent.fragment;

      // the id might be scoped
      elemId.split("/").forEach(function(id) {
        node = node.querySelector('[id="' + id + '"]');
      });

      if (node) this.editFragmentText(node);
    },

    editFragmentText: function(fragment) {
      this.fragment = fragment;

      // disable the edit button
      this.$('.btn.edit-text').prop('disabled', true);

      // ensure source code is hidden
      this.$('.btn.show-source.active').click();

      var self = this;
      var $editable = this.$('.akoma-ntoso').children().first();
      // text from node in the actual XML document
      var text = this.xmlToText(this.fragment);

      // adjust menu items
      this.$menu.find('.text-editor-only').removeClass('disabled');

      // show the text editor
      this.$('.document-content-view, .document-content-header')
        .addClass('show-text-editor')
        .find('.toggle-editor-buttons .btn')
        .prop('disabled', true);

      this.$textEditor
        .data('fragment', this.fragment.tagName)
        .show();

      this.textEditor.setValue(text);
      this.textEditor.gotoLine(1, 0);
      this.textEditor.focus();

      this.$('.document-sheet-container').scrollTop(0);
    },

    xmlToText: function(element) {
      return this.textTransform
        .transformToFragment(element, document)
        .firstChild.textContent
        // cleanup inline whitespace
        .replace(/([^ ]) +/g, '$1 ')
        // remove multiple consecutive blank lines
        .replace(/^( *\n){2,}/gm, "\n");
    },

    saveTextEditor: function(e) {
      var self = this;
      var $editable = this.$('.akoma-ntoso').children().first();
      var $btn = this.$('.text-editor-buttons .btn.save');
      var content = this.textEditor.getValue();
      var fragment = this.$textEditor.data('fragment');
      fragment = this.grammar_fragments[fragment] || fragment;

      // should we delete the item?
      if (!content.trim() && fragment != 'akomaNtoso') {
        if (confirm('Go ahead and delete this section from the document?')) {
          this.parent.removeFragment(this.fragment);
        }
        return;
      }

      $btn
        .attr('disabled', true)
        .find('.fa')
          .removeClass('fa-check')
          .addClass('fa-spinner fa-pulse');

      // The actual response to update the view is done
      // in a deferred so that we can cancel it if the
      // user clicks 'cancel'
      var deferred = this.pendingTextSave = $.Deferred();
      deferred
        .then(function(response) {
          var newFragment = $.parseXML(response.output);

          if (fragment === 'akomaNtoso') {
            // entire document
            newFragment = [newFragment.documentElement];
          } else {
            newFragment = newFragment.documentElement.children;
          }

          self.parent.updateFragment(self.fragment, newFragment);
          self.closeTextEditor();
          self.render();
          self.setXmlEditorValue(Indigo.toXml(newFragment[0]));
        })
        .fail(function(xhr, status, error) {
          // this will be null if we've been cancelled without an ajax response
          if (xhr) {
            if (xhr.status == 400) {
              Indigo.errorView.show(xhr.responseJSON.content || error || status);
            } else {
              Indigo.errorView.show(error || status);
            }
          }
        })
        .always(function() {
          // TODO: this doesn't feel like it's in the right place;
          $btn
            .attr('disabled', false)
            .find('.fa')
              .removeClass('fa-spinner fa-pulse')
              .addClass('fa-check');
        });

      var data = {
        'content': content,
      };
      if (fragment != 'akomaNtoso') {
        data.fragment = fragment;
      }

      $.ajax({
        url: '/api/parse',
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"})
        .done(function(response) {
          deferred.resolve(response);
        })
        .fail(function(xhr, status, error) {
          deferred.reject(xhr, status, error);
        });
    },

    closeTextEditor: function(e) {
      if (this.pendingTextSave) {
        this.pendingTextSave.reject();
        this.pendingTextSave = null;
      }

      this.$('.document-content-view, .document-content-header')
        .removeClass('show-text-editor')
        .find('.toggle-editor-buttons .btn')
        .prop('disabled', false);

      // adjust menu items
      this.$menu.find('.text-editor-only').addClass('disabled');
    },

    editFragment: function(node) {
      // edit node, a node in the XML document
      this.tableEditor.discardChanges();
      this.closeTextEditor();
      this.render();
      this.$('.document-sheet-container').scrollTop(0);

      this.setXmlEditorValue(Indigo.toXml(node));
    },

    setXmlEditorValue: function(xml) {
      // pretty-print the xml
      xml = prettyPrintXml(xml);

      this.xmlEditor.removeListener('change', this.onEditorChange);
      this.xmlEditor.setValue(xml);
      this.xmlEditor.on('change', this.onEditorChange);
    },

    xmlEditorChanged: function() {
      // save the contents of the XML editor
      console.log('Parsing changes to XML');

      // TODO: handle errors here
      var newFragment = $.parseXML(this.xmlEditor.getValue()).documentElement;

      this.parent.updateFragment(this.parent.fragment, [newFragment]);
      this.render();
    },

    // Save the content of the XML editor into the DOM, returns a Deferred
    saveChanges: function() {
      this.tableEditor.saveChanges();
      this.closeTextEditor();
      return $.Deferred().resolve();
    },

    // Discard the content of the editor, returns a Deferred
    discardChanges: function() {
      this.tableEditor.discardChanges();
      this.closeTextEditor();
      return $.Deferred().resolve();
    },

    render: function() {
      if (this.htmlTransform && this.parent.fragment) {
        this.htmlTransform.setParameter(null, 'defaultIdScope', this.getFragmentIdScope() || '');
        this.htmlTransform.setParameter(null, 'manifestationUrl', this.parent.model.manifestationUrl());
        this.htmlTransform.setParameter(null, 'lang', this.parent.model.get('language'));
        var html = this.htmlTransform.transformToFragment(this.parent.fragment, document);

        this.makeLinksExternal(html);
        this.makeTablesEditable(html);
        this.makeElementsQuickEditable(html);
        this.$('.akoma-ntoso').empty().get(0).appendChild(html);
        this.trigger('rendered');
      }
    },

    getFragmentIdScope: function() {
      // default scope for ID elements
      var ns = this.parent.fragment.namespaceURI;
      var idScope = this.parent.fragment.ownerDocument.evaluate(
        "./ancestor::a:doc[@name][1]/@name",
        this.parent.fragment,
        function(x) { if (x == "a") return ns; },
        XPathResult.ANY_TYPE,
        null);

      idScope = idScope.iterateNext();
      return idScope ? idScope.value : null;
    },

    makeLinksExternal: function(html) {
      html.querySelectorAll('a').forEach(function(a) {
        a.setAttribute("target", "_blank");
        $(a).tooltip({title: a.getAttribute('data-href')});
      });
    },

    makeTablesEditable: function(html) {
      var tables = html.querySelectorAll('table[id]'),
          self = this;

      tables.forEach(function(table) {
        var w = self.tableEditor.tableWrapper.cloneNode(true),
            $w = $(w);

        $w.find('button').data('table-id', table.id);
        table.insertAdjacentElement('beforebegin', w);
        // we bind the CKEditor instance to this div, since CKEditor can't be
        // directly attached to the table element
        $w.find('.table-container').append(table);
      });
    },

    makeElementsQuickEditable: function(html) {
      $(html.firstElementChild)
        .find(this.quickEditable)
        .addClass('quick-editable')
        .prepend(this.quickEditTemplate);
    },

    editTable: function(e) {
      var $btn = $(e.currentTarget),
          table = document.getElementById($btn.data('table-id'));
      this.tableEditor.editTable(table);
      // disable other table edit buttons
      this.$('.edit-table').prop('disabled', true);
    },

    tableEditStart: function() {
      this.$('.edit-text').hide();
    },

    tableEditFinish: function() {
      this.$('.edit-text').show();
      // enable all table edit buttons
      this.$('.edit-table').prop('disabled', false);
    },

    editFind: function(e) {
      e.preventDefault();
      this.textEditor.execCommand('find');
    },

    editFindNext: function(e) {
      e.preventDefault();
      this.textEditor.execCommand('findnext');
    },

    editFindPrevious: function(e) {
      e.preventDefault();
      this.textEditor.execCommand('findprevious');
    },

    editFindReplace: function(e) {
      e.preventDefault();
      this.textEditor.execCommand('replace');
    },

    /**
     * Setup the box to insert an image into the document text.
     */
    insertImage: function(e) {
      var self = this;

      e.preventDefault();

      if (!this.insertImageBox) {
        // setup insert-image box
        this.insertImageBox = new Indigo.InsertImageView({document: this.parent.model});
      }

      // are we on an image tag in the editor?
      var posn = this.textEditor.getCursorPosition(),
          session = this.textEditor.getSession(),
          token = session.getTokenAt(posn.row, posn.column),
          selected = null,
          alt_text = "", filename, parts;

      if (token && token.type == "constant.other.image") {
        parts = token.value.split(/[[()\]]/);
        alt_text = parts[1];
        filename = parts[3];
        if (filename.startsWith("media/")) filename = filename.substr(6);

        selected = this.parent.model.attachments().findWhere({filename: filename});
      } else {
        token = null;
      }

      this.insertImageBox.show(function(image) {
        var tag = "![" + (alt_text) + "](media/" + image.get('filename') + ")";

        if (token) {
          // replace existing image
          var Range = ace.require("ace/range").Range;
          var range = new Range(posn.row, token.start, posn.row, token.start + token.value.length);
          session.getDocument().replace(range, tag);
        } else {
          // new image
          self.textEditor.insert(tag);
        }

        self.textEditor.focus();
      }, selected);
    },

    insertTable: function(e) {
      e.preventDefault();

      var table = ["{|", "|-", "! heading 1", "! heading 2", "|-", "| cell 1", "| cell 2", "|-", "| cell 3", "| cell 4", "|-", "|}", ""],
          posn = this.textEditor.getCursorPosition(),
          range = this.textEditor.getSelectionRange();

      this.textEditor.clearSelection();

      table = "\n{|\n|-\n";
      var lines = this.textEditor.getSession().getTextRange(range).split("\n");
      lines.forEach(function(line) {
        table = table + "| " + line + "\n|-\n";
      });
      table = table + "|}\n";
      this.textEditor.getSession().replace(range, table);

      this.textEditor.moveCursorTo(posn.row + 3, 2);
      this.textEditor.focus();
    },

    resize: function() {},
  });


  // Handle the document editor, tracking changes and saving it back to the server.
  // The model is an Indigo.DocumentContent instance.
  Indigo.DocumentEditorView = Backbone.View.extend({
    el: '#content-tab',
    events: {
      'click .btn.show-fullscreen': 'toggleFullscreen',
      'click .btn.show-source': 'toggleShowCode',
    },

    initialize: function(options) {
      this.dirty = false;
      this.editing = false;

      this.documentContent = options.documentContent;
      // XXX: check
      this.documentContent.on('change', this.setDirty, this);
      this.documentContent.on('sync', this.setClean, this);

      this.tocView = options.tocView;
      this.tocView.on('item-selected', this.editTocItem, this);

      // setup the editor views
      this.sourceEditor = new Indigo.SourceEditorView({parent: this});

      this.showDocumentSheet();
    },

    editTocItem: function(item) {
      var self = this;
      this.stopEditing()
        .then(function() {
          if (item) {
            self.$el.find('.boxed-group-header h4').text(item.title);
            self.editFragment(item.element);
          }
        });
    },

    stopEditing: function() {
      if (this.activeEditor && this.editing) {
        this.editing = false;
        return this.activeEditor.discardChanges();
      } else {
        this.editing = false;
        return $.Deferred().resolve();
      }
    },

    editFragment: function(fragment) {
      if (!this.updating && fragment) {
        console.log("Editing new fragment");
        this.editing = true;
        this.fragment = fragment;
        this.activeEditor.editFragment(fragment);
      }
    },

    toggleFullscreen: function(e) {
      this.$el.toggleClass('fullscreen');
      this.activeEditor.resize();
    },

    toggleShowCode: function(e) {
      if (this.activeEditor.name == 'source') {
        this.$el.find('.document-content-view').toggleClass('show-source');
      }
    },

    removeFragment: function(fragment) {
      fragment = fragment || this.fragment;
      this.documentContent.replaceNode(fragment, null);
    },

    updateFragment: function(oldNode, newNodes) {
      this.updating = true;
      try {
        var updated = this.documentContent.replaceNode(oldNode, newNodes);
        if (oldNode == this.fragment) {
          this.fragment = updated;
        }
      } finally {
        this.updating = false;
      }
    },

    showDocumentSheet: function() {
      var self = this;

      this.stopEditing()
        .then(function() {
          self.$el.find('.sheet-editor').addClass('in');
          self.$el.find('.btn.show-source, .btn.edit-text').prop('disabled', false);
          self.$el.find('.btn.edit-text').addClass('btn-warning').removeClass('btn-default');
          self.activeEditor = self.sourceEditor;
          self.editFragment(self.fragment);
        });
    },

    setDirty: function() {
      if (!this.dirty) {
        this.dirty = true;
        this.trigger('dirty');
      }
    },

    setClean: function() {
      if (this.dirty) {
        this.dirty = false;
        this.trigger('clean');
      }
    },

    // Save the content of the editor, returns a Deferred
    save: function() {
      var self = this;

      // don't do anything if it hasn't changed
      if (!this.dirty) {
        return $.Deferred().resolve();
      }

      if (this.activeEditor) {
        return this.activeEditor
          // ask the editor to returns its contents
          .saveChanges()
          .then(function() {
            // save the model
            return self.saveModel();
          });
      } else {
        return this.saveModel();
      }
    },

    // Save the content of the document, returns a Deferred
    saveModel: function() {
      return this.documentContent.save();
    },
  });
})(window);
