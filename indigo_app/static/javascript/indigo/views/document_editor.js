(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // The SourceEditorView manages the interaction between
  // the model, the wrapping document editor view, and the source (xml) and
  // text editor components.
  Indigo.SourceEditorView = Backbone.View.extend({
    el: 'body',
    events: {
      'click .text-editor-buttons .btn.save': 'saveTextEditor',
      'click .text-editor-buttons .btn.cancel': 'closeTextEditor',
      'click .btn.edit-text': 'fullEdit',
      'click .btn.edit-table': 'editTable',
      'click .quick-edit': 'quickEdit',

      'click .edit-find': 'editFind',
      'click .edit-find-next': 'editFindNext',
      'click .edit-find-previous': 'editFindPrevious',
      'click .edit-find-replace': 'editFindReplace',

      'click .insert-image': 'insertImage',
      'click .insert-table': 'insertTable',
      'click .insert-schedule': 'insertSchedule',

      'click .markup-remark': 'markupRemark',
      'click .markup-bold': 'markupBold',
      'click .markup-italics': 'markupItalics',
    },

    initialize: function(options) {
      var self = this;

      this.parent = options.parent;
      this.name = 'source';
      this.editing = false;
      this.quickEditTemplate = $('<a href="#" class="quick-edit"><i class="fas fa-pencil-alt"></i></a>')[0];

      // setup renderer
      this.editorReady = $.Deferred();
      this.listenTo(this.parent.model, 'change', this.documentChanged);

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
      this.textEditor.setValue();
      this.textEditor.getSession().setUseWrapMode(true);
      this.textEditor.setShowPrintMargin(false);
      this.textEditor.$blockScrolling = Infinity;

      // setup table editor
      this.tableEditor = new Indigo.TableEditorView({parent: this, documentContent: this.parent.documentContent});
      this.tableEditor.on('start', this.tableEditStart, this);
      this.tableEditor.on('finish', this.tableEditFinish, this);
      this.setupTablePasting();

      this.$toolbar = $('.document-editor-toolbar');

      this.loadXSL();
      this.textEditor.getSession().setMode(this.parent.model.tradition().settings.grammar.aceMode);
    },

    /* Setup pasting so that when the user pastes an HTML table
       while in text edit mode, we change it into wikipedia style tables.

       We cannot disable the Ace editor paste functionality. Instead, we
       bypass it by pretending there is no text to paste. Then, we handle
       the paste event itself and re-inject the correct text to paste.
     */
    setupTablePasting: function() {
      var allowPaste = false,
          self = this;

      this.textEditor.on('paste', function(e) {
        if (!allowPaste) { e.text = ''; }
      });

      this.$textEditor.on('paste', function(e) {
        var cb = e.originalEvent.clipboardData;

        function pasteTable(table) {
          self.xmlToText(self.tableEditor.tableToAkn(table)).then(function (text) {
            if (t > 0) text = "\n" + text;

            allowPaste = true;
            self.textEditor.onPaste(text);
            allowPaste = false;
          });
        }

        if (cb.types.indexOf('text/html') > -1) {
          var doc = new DOMParser().parseFromString(cb.getData('text/html'), 'text/html'),
              tables = doc.body.querySelectorAll('table');

          if (tables.length > 0) {
            for (var t = 0; t < tables.length; t++) {
              var table = tables[t];

              // strip out non HTML tags - we don't want MS Office's tags
              var elems = table.getElementsByTagName("*");
              for (var i = 0; i < elems.length; i++) {
                if (elems[i].tagName.indexOf(':') > -1) elems[i].remove();
              }

              pasteTable(table);
            }

            return;
          }
        }

        // no html or no tables, use normal paste
        allowPaste = true;
        self.textEditor.onPaste(cb.getData('text'));
        allowPaste = false;
      });
    },

    documentChanged: function() {
      this.coverpageCache = null;
      this.render();
    },

    loadXSL: function() {
      var country = this.parent.model.get('country'),
          self = this;

      // setup akn to html transform
      this.htmlTransformReady = $.Deferred();
      function htmlLoaded(xml) {
        var htmlTransform = new XSLTProcessor();
        htmlTransform.importStylesheet(xml);
        htmlTransform.setParameter(null, 'resolverUrl', '/works');

        self.htmlTransform = htmlTransform;
        self.editorReady.resolve();
        self.htmlTransformReady.resolve();
      }

      $.get('/static/xsl/act-' + country +'.xsl')
        .then(htmlLoaded)
        .fail(function() {
          $.get('/static/xsl/act.xsl')
            .then(htmlLoaded);
        });


      // setup akn to text transform
      this.textTransformReady = $.Deferred();
      function textLoaded(xml) {
        var textTransform = new XSLTProcessor();
        textTransform.importStylesheet(xml);

        self.textTransform = textTransform;
        self.textTransformReady.resolve();
      }

      $.get('/static/xsl/act_text-' + country +'.xsl')
        .then(textLoaded)
        .fail(function() {
          $.get('/static/xsl/act_text.xsl')
            .then(textLoaded);
        });
    },

    fullEdit: function(e) {
      e.preventDefault();
      this.editFragmentText(this.parent.fragment);
    },

    quickEdit: function(e) {
      var elemId = e.currentTarget.parentElement.parentElement.id,
          node = this.parent.documentContent.xmlDocument;

      // the id might be scoped
      elemId.split("/").forEach(function(id) {
        node = node.querySelector('[id="' + id + '"]');
      });

      if (node) this.editFragmentText(node);
    },

    editFragmentText: function(fragment) {
      var self = this;

      this.editing = true;
      this.fragment = fragment;

      // ensure source code is hidden
      this.$('.btn.show-xml-editor.active').click();

      // show the edit toolbar
      this.$toolbar.find('.btn-toolbar').addClass('d-none');
      this.$toolbar.find('.text-editor-buttons').removeClass('d-none');
      this.$('.document-workspace-buttons').addClass('d-none');

      var $editable = this.$('.document-workspace-content .akoma-ntoso').children().first();
      // text from node in the actual XML document
      this.xmlToText(this.fragment).then(function(text) {
        // show the text editor
        self.$('.document-content-view').addClass('show-text-editor');

        self.$textEditor
          .data('fragment', self.fragment.tagName)
          .show();

        self.textEditor.setValue(text);
        self.textEditor.gotoLine(1, 0);
        self.textEditor.focus();

        self.$('.document-sheet-container').scrollTop(0);
      });
    },

    xmlToText: function(element) {
      var self = this,
          deferred = $.Deferred();

      this.textTransformReady.then(function() {
        var text = self.textTransform
          .transformToFragment(element, document)
          .firstChild.textContent
          // remove multiple consecutive blank lines
          .replace(/^( *\n){2,}/gm, "\n");

        deferred.resolve(text);
      });

      return deferred;
    },

    saveTextEditor: function(e) {
      var self = this;
      var $editable = this.$('.document-workspace-content .akoma-ntoso').children().first();
      var $btn = this.$('.text-editor-buttons .btn.save');
      var content = this.textEditor.getValue();
      var fragmentRule = this.parent.model.tradition().grammarRule(this.fragment);

      // should we delete the item?
      if (!content.trim() && fragmentRule != 'akomaNtoso') {
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

          if (fragmentRule === 'akomaNtoso') {
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

      var id = this.fragment.getAttribute('id'),
          data = {
        'content': content,
        'frbr_uri': this.parent.model.get('frbr_uri'),
      };
      if (fragmentRule != 'akomaNtoso') {
        data.fragment = fragmentRule;
        if (id && id.lastIndexOf('.') > -1) {
          // retain the id of the parent element as the prefix
          data.id_prefix = id.substring(0, id.lastIndexOf('.'));
        }
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

      this.$('.document-content-view').removeClass('show-text-editor');

      // adjust the toolbar
      this.$toolbar.find('.btn-toolbar').addClass('d-none');
      this.$toolbar.find('.general-buttons').removeClass('d-none');
      this.$('.document-workspace-buttons').removeClass('d-none');

      this.editing = false;
    },

    editFragment: function(node) {
      // edit node, a node in the XML document
      this.tableEditor.discardChanges(null, true);
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
      this.tableEditor.discardChanges(null, true);
      this.closeTextEditor();
      return $.Deferred().resolve();
    },

    render: function() {
      if (!this.parent.fragment) return;

      var self = this,
          renderCoverpage = this.parent.fragment.parentElement === null,
          $akn = this.$('.document-workspace-content .akoma-ntoso'),
          coverpage;

      // reset class name to ensure only one country class
      $akn[0].className = "akoma-ntoso spinner-when-empty country-" + this.parent.model.get('country');
      $akn.empty();

      if (renderCoverpage) {
        coverpage = document.createElement('div');
        coverpage.className = 'spinner-when-empty';
        $akn.append(coverpage);
        this.renderCoverpage().then(function(node) {
          $(coverpage).append(node);
        });
      }

      this.htmlTransformReady.then(function() {
        self.htmlTransform.setParameter(null, 'defaultIdScope', self.getFragmentIdScope() || '');
        self.htmlTransform.setParameter(null, 'mediaUrl', self.parent.model.url() + '/');
        self.htmlTransform.setParameter(null, 'lang', self.parent.model.get('language'));
        self.htmlTransform.setParameter(null, 'documentType', self.parent.model.work.get('nature'));
        self.htmlTransform.setParameter(null, 'subtype', self.parent.model.get('subtype') || '');
        self.htmlTransform.setParameter(null, 'country', self.parent.model.work.get('country'));
        self.htmlTransform.setParameter(null, 'locality', self.parent.model.work.get('locality') || '');
        var html = self.htmlTransform.transformToFragment(self.parent.fragment, document);

        self.makeLinksExternal(html);
        self.addWorkPopups(html);
        self.makeTablesEditable(html);
        self.makeElementsQuickEditable(html);
        $akn.append(html);
        
        self.trigger('rendered');
      });

      // HACK HACK HACK
      var data = {};
      data.document = this.parent.model.toJSON();
      data.document.content = this.parent.documentContent.toXml();
      data.element_id = this.parent.fragment.getAttribute('id');

      $.ajax({
        url: '/api/documents/278/diff',
        type: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json"})
          .then(function(response) {
            var html = $.parseHTML(response.html_diff)[0];

            // TODO: handle comments
            
            self.makeLinksExternal(html);
            self.addWorkPopups(html);
            self.makeTablesEditable(html);
            self.makeElementsQuickEditable(html);
            $akn.empty();
            $akn.addClass('diffset');
            $akn.append(html);

            self.trigger('rendered');
          });
    },

    renderCoverpage: function() {
      // Render a coverpage and return it via a deferred.
      // Uses a cached coverpage, if available.
      var deferred = $.Deferred(),
          self = this;

      if (this.coverpageCache) {
        deferred.resolve(this.coverpageCache);
      } else {
        var data = JSON.stringify({'document': self.parent.model.toJSON()});
        $.ajax({
          url: '/api/render/coverpage',
          type: "POST",
          data: data,
          contentType: "application/json; charset=utf-8",
          dataType: "json"})
          .then(function(response) {
            var html = $.parseHTML(response.output);
            self.coverpageCache = html;
            deferred.resolve(html);
          });
      }

      return deferred;
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
      html.querySelectorAll('a[href]').forEach(function(a) {
        if (!a.getAttribute('href').startsWith('#')) {
          a.setAttribute("target", "_blank");
          $(a).tooltip({title: a.getAttribute('data-href') || a.getAttribute('href')});
        }
      });
    },

    addWorkPopups: function(html) {
      html.querySelectorAll('a[href^="/works/"]').forEach(function(a) {
        a.setAttribute("data-popup-url", a.href + '/popup');
        $(a).tooltip('disable');
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
      var self = this;

      $(html.firstElementChild)
        .find(this.parent.model.tradition().settings.grammar.quickEditable)
        .addClass('quick-editable')
        .each(function(i, e) {
          self.ensureGutterActions(e).append(self.quickEditTemplate.cloneNode(true));
        });
    },

    // Ensure this element has a gutter actions child
    ensureGutterActions: function(elem) {
      if (!elem.firstElementChild || !elem.firstElementChild.classList.contains('gutter-actions')) {
        var div = document.createElement('div');
        div.className = 'gutter-actions ig';
        elem.prepend(div);
      }

      return elem.firstElementChild;
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

      // adjust the toolbar
      this.$toolbar.find('.btn-toolbar').addClass('d-none');
      this.$('.document-workspace-buttons').addClass('d-none');

      this.editing = true;
    },

    tableEditFinish: function() {
      this.$('.edit-text').show();
      // enable all table edit buttons
      this.$('.edit-table').prop('disabled', false);

      // adjust the toolbar
      this.$toolbar.find('.btn-toolbar').addClass('d-none');
      this.$toolbar.find('.general-buttons').removeClass('d-none');
      this.$('.document-workspace-buttons').removeClass('d-none');

      this.editing = false;
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

      var table,
          posn = this.textEditor.getCursorPosition(),
          range = this.textEditor.getSelectionRange();

      if (this.textEditor.getSelectedText().length > 0) {
        this.textEditor.clearSelection();

        table = "\n{|\n|-\n";
        var lines = this.textEditor.getSession().getTextRange(range).split("\n");
        lines.forEach(function(line) {
          // ignore empty lines
          if (line.trim() !== "") {
            table = table + "| " + line + "\n|-\n";
          }
        });
        table = table + "|}\n";
      } else {
        table = ["", "{|", "|-", "! heading 1", "! heading 2", "|-", "| cell 1", "| cell 2", "|-", "| cell 3", "| cell 4", "|-", "|}", ""].join("\n");
      }

      this.textEditor.getSession().replace(range, table);

      this.textEditor.moveCursorTo(posn.row + 3, 2);
      this.textEditor.focus();
    },

    insertSchedule: function(e) {
      e.preventDefault();

      this.textEditor.insert('\nSCHEDULE - <optional schedule name>\n<optional schedule title>\n\n');
      this.textEditor.focus();
    },

    quickMarkup: function(marker) {
      var range = this.textEditor.getSelectionRange();

      if (this.textEditor.getSelectedText().length > 0) {
        this.textEditor.clearSelection();

        var text = this.textEditor.getSession().getTextRange(range);
        this.textEditor.getSession().replace(range, marker(text));
      } else {
        this.textEditor.insert(marker(''));
      }
    },

    markupRemark: function(e) {
      e.preventDefault();

      this.quickMarkup(function(text) {
        return '[[' + (text || '<remark>') + ']]';
      });
      this.textEditor.focus();
    },

    markupBold: function(e) {
      e.preventDefault();

      this.quickMarkup(function(text) {
        return '**' + (text || '<text>') + '**';
      });
      this.textEditor.focus();
    },

    markupItalics: function(e) {
      e.preventDefault();

      this.quickMarkup(function(text) {
        return '//' + (text || '<text>') + '//';
      });
      this.textEditor.focus();
    },

    resize: function() {},
  });


  // Handle the document editor, tracking changes and saving it back to the server.
  // The model is an Indigo.DocumentContent instance.
  Indigo.DocumentEditorView = Backbone.View.extend({
    el: 'body',
    events: {
      'click .btn.show-xml-editor': 'toggleShowXMLEditor',
      'click .btn.show-akn-hierarchy': 'toggleShowAKNHierarchy',
    },

    initialize: function(options) {
      this.dirty = false;

      this.documentContent = options.documentContent;
      // XXX: check
      this.documentContent.on('change', this.setDirty, this);
      this.documentContent.on('sync', this.setClean, this);

      this.tocView = options.tocView;
      this.tocView.selection.on('change', this.tocSelectionChanged, this);

      // setup the editor views
      this.sourceEditor = new Indigo.SourceEditorView({parent: this});
      // XXX this is a deferred to indicate when the editor is ready to edit
      this.editorReady = this.sourceEditor.editorReady;
      this.editFragment(null);
    },

    tocSelectionChanged: function(selection) {
      var self = this;

      this.stopEditing()
        .then(function() {
          if (selection) {
            self.editFragment(selection.get('element'));
          }
        });
    },

    stopEditing: function() {
      return this.sourceEditor.discardChanges();
    },

    editFragment: function(fragment) {
      if (!this.updating && fragment) {
        console.log("Editing new fragment");

        var isRoot = fragment.parentElement === null;

        this.fragment = fragment;
        this.$('.document-content-view .document-sheet-container .sheet-inner').toggleClass('is-fragment', !isRoot);

        this.sourceEditor.editFragment(fragment);
      }
    },

    toggleShowXMLEditor: function(e) {
      var show = !$(e.currentTarget).hasClass('active');
      this.$el.find('.document-content-view').toggleClass('show-xml-editor', show);
      this.$el.find('.document-content-view .annotations-container').toggleClass('hide-annotations', show);
    },

    toggleShowAKNHierarchy: function(e) {
      var show = !$(e.currentTarget).hasClass('active');
      this.$el.find('#document-sheet').toggleClass('show-akn-hierarchy', show);
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

    isDirty: function() {
      return this.dirty || this.sourceEditor.editing;
    },

    canCancelEdits: function() {
      return (!this.sourceEditor.editing || confirm("You will lose your changes, are you sure?"));
    },

    // Save the content of the editor, returns a Deferred
    save: function() {
      var self = this,
          deferred = $.Deferred();

      function ok() { deferred.resolve(); }
      function fail() { deferred.reject(); }

      if (!this.dirty) {
        // don't do anything if it hasn't changed
        ok();

      } else {
        this.sourceEditor
          // ask the editor to returns its contents
          .saveChanges()
          .done(function() {
            // save the model
            self.saveModel().done(ok).fail(fail);
          })
          .fail(fail);
      }

      return deferred;
    },

    // Save the content of the document, returns a Deferred
    saveModel: function() {
      return this.documentContent.save();
    },
  });
})(window);
