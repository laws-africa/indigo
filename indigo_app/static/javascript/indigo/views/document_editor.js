(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // The AceEditorController manages the interaction between
  // the ace-based editor, the model, and the document editor view.
  //
  // It also handles the in-place text-based editor.
  Indigo.AceEditorController = function(options) {
    this.initialize.apply(this, arguments);
  };
  _.extend(Indigo.AceEditorController.prototype, Backbone.Events, {
    initialize: function(options) {
      var self = this;

      this.view = options.view;

      this.editor = ace.edit(this.view.$el.find(".ace-editor")[0]);
      this.editor.setTheme("ace/theme/monokai");
      this.editor.getSession().setMode("ace/mode/xml");
      this.editor.setValue();
      this.editor.$blockScrolling = Infinity;
      this.onEditorChange = _.debounce(_.bind(this.editorChanged, this), 500);

      // setup renderer
      var htmlTransform = new XSLTProcessor();
      $.get('/static/xsl/act.xsl')
        .then(function(xml) {
          htmlTransform.importStylesheet(xml);
          self.htmlTransform = htmlTransform;
        });

      // setup inline sheet editor
      this.$inlineEditor = this.view.$el.find('#inline-editor');
      this.$inlineEditor.find('.btn.save').on('click', _.bind(this.saveInlineEditor, this));
      this.$inlineEditor.find('.btn.cancel').on('click', _.bind(this.closeInlineEditor, this));

      this.$inlineButtons = this.view.$el.find('.document-sheet-buttons');
      this.$inlineButtons.find('.edit').on('click', _.bind(this.editInline, this));

      var textTransform = new XSLTProcessor();
      $.get('/static/xsl/act_text.xsl')
        .then(function(xml) {
          textTransform.importStylesheet(xml);
          self.textTransform = textTransform;
        });
    },

    editInline: function(e) {
      e.preventDefault();

      var self = this;
      var $editable = this.view.$el.find('.an-container').children().first();

      // text from node in the actual XML document
      var text = this.textTransform
        .transformToFragment(this.view.fragment, document)
        .firstChild.textContent
        // cleanup inline whitespace
        .replace(/([^ ]) +/g, '$1 ')
        // remove multiple consecutive blank lines
        .replace(/^( *\n){2,}/gm, "\n");

      // show the inline editor
      $editable.css({position: 'relative'});
      this.$inlineEditor
        .data('fragment', this.view.fragment.tagName)
        .height($editable.height())
        .width($editable.width())
        .appendTo($editable)
        .show()
        .find('textarea')
          .val(text)
          .focus()
          .caret(0)
          .scrollTop(0);

      this.view.$el.find('.document-sheet-container').scrollTop(0);
      this.$inlineButtons.hide();
    },

    saveInlineEditor: function(e) {
      var self = this;
      var $editable = this.view.$el.find('.an-container').children().first();
      var $btn = this.$inlineEditor.find('.btn.save');
      var fragment = this.$inlineEditor.data('fragment');

      var data = JSON.stringify({
        'inputformat': 'text/plain',
        'outputformat': 'application/xml',
        'fragment': fragment,
        'content': this.$inlineEditor.find('textarea').val(),
      });

      $btn
        .attr('disabled', true)
        .find('.fa')
          .removeClass('fa-check')
          .addClass('fa-spinner fa-pulse');

      $.ajax({
        url: '/api/convert',
        type: "POST",
        data: data,
        contentType: "application/json; charset=utf-8",
        dataType: "json"})
        .then(function(response) {
          // find either the fragment we asked for, or the first element below the akomaNtoso
          // parent element
          var newFragment = $.parseXML(response.output);
          newFragment = newFragment.querySelector(fragment) || newFragment.documentElement.firstElementChild;

          self.view.updateFragment(self.view.fragment, newFragment);
          self.closeInlineEditor();
          self.render();
          self.setEditorValue(self.view.xmlModel.toXml(newFragment));
        })
        .fail(function(xhr, status, error) {
          if (xhr.status == 400) {
            Indigo.errorView.show(xhr.responseJSON.content || error || status);
          } else {
            Indigo.errorView.show(error || status);
          }
        })
        .always(function(response) {
          $btn
            .attr('disabled', false)
            .find('.fa')
              .removeClass('fa-spinner fa-pulse')
              .addClass('fa-check');
        });
    },

    closeInlineEditor: function(e) {
      this.$inlineEditor.hide();
      this.view.$el.find('.document-sheet-container').after(this.$inlineEditor);

      this.$inlineButtons.show();
    },

    editFragment: function(node) {
      // edit node, a node in the XML document
      this.closeInlineEditor();
      this.render();
      this.view.$el.find('.document-sheet-container').scrollTop(0);

      this.dirty = false;
      var xml = this.view.xmlModel.toXml(node);
      this.setEditorValue(xml);
    },

    setEditorValue: function(xml) {
      // pretty-print the xml
      xml = prettyPrintXml(xml);

      this.editor.removeListener('change', this.onEditorChange);
      this.editor.setValue(xml);
      this.editor.on('change', this.onEditorChange);
    },

    editorChanged: function() {
      this.dirty = true;
      this.saveChanges();
    },

    // Save the content of the XML editor into the DOM, returns a Deferred
    saveChanges: function() {
      this.closeInlineEditor();

      if (this.dirty) {
        // update the fragment content from the editor's version
        console.log('Parsing changes to XML');

        // TODO: handle errors here
        var newFragment = $.parseXML(this.editor.getValue()).documentElement;

        this.view.updateFragment(this.view.fragment, newFragment);
        this.render();
        this.dirty = false;
      }

      return $.Deferred().resolve();
    },

    render: function() {
      if (this.htmlTransform && this.view.fragment) {
        var html = this.htmlTransform.transformToFragment(this.view.fragment, document);
        this.view.$el.find('.an-container').html('').get(0).appendChild(html);
      }
    },

    resize: function() {},
  });

  // The LimeEditorController manages the interaction between
  // the LIME-based editor, the model, and the document editor view.
  Indigo.LimeEditorController = function(options) {
    this.initialize.apply(this, arguments);
  };
  _.extend(Indigo.LimeEditorController.prototype, Backbone.Events, {
    initialize: function(options) {
      this.view = options.view;
      this.initialized = false;
    },

    editFragment: function(node) {
      // if we're editing the entire document,
      // strip the metadata when we next edit the 
      this.stripMeta = !node.querySelector('meta');
      this.fragmentType = node.tagName;
      this.editing = true;

      this.resize();

      // We only want to interact with the editor once the document
      // is fully loaded, which we get as a callback from the
      // application. We only setup this event handler once.
      this.loading = true;
      if (!this.initialized) {
        LIME.app.on('documentLoaded', this.documentLoaded, this);
        this.initialized = true;
      }

      var config = {
        docMarkingLanguage: "akoma2.0",
        docType: "act",
        docLocale: this.view.model.get('country'),
        docLang: "eng",
      };

      LIME.XsltTransforms.transform(
        node,
        LIME_base_url + 'languagesPlugins/akoma2.0/AknToXhtml.xsl',
        {},
        function(html) {
          config.docText = html.firstChild.outerHTML;
          LIME.app.fireEvent("loadDocument", config);
        }
      );
    },

    documentLoaded: function() {
      // document has loaded
      this.loading = false;
    },

    // Save the content of the LIME editor into the DOM, returns a Deferred
    updateFromLime: function() {
      var self = this;
      var start = new Date().getTime();
      var oldFragment = this.view.fragment;
      var deferred = $.Deferred();

      console.log('Updating XML from LIME');

      LIME.app.fireEvent("translateRequest", function(xml) {
        var stop = new Date().getTime();
        console.log('Got XML from LIME in ' + (stop-start) + ' msecs');

        // reset the changed flag
        LIME.app.getController('Editor').changed = false;

        if (self.stripMeta) {
          // We're editing just a fragment.
          // LIME inserts a meta element which we need to strip.
          var meta = xml.querySelector('meta');
          if (meta) {
            meta.remove();
          }
        }

        // LIME wraps the document in some extra stuff, just find the
        // item we started with
        xml = xml.querySelector(self.fragmentType);
        self.view.updateFragment(oldFragment, xml);

        deferred.resolve();
      }, {
        serialize: false,
      });

      return deferred;
    },

    // Save the content of the LIME editor into the DOM, returns a Deferred
    saveChanges: function() {
      if (!this.loading) {
        return this.updateFromLime();
      } else {
        return $.Deferred().resolve();
      }
    },

    resize: function() {
      LIME.app.resize();
    },
  });


  // Handle the document editor, tracking changes and saving it back to the server.
  // The model is an Indigo.DocumentContent instance.
  Indigo.DocumentEditorView = Backbone.View.extend({
    el: '#content-tab',
    events: {
      'change [value=plaintext]': 'editWithAce',
      'change [value=lime]': 'editWithLime',
      'change [name=fullscreen]': 'toggleFullscreen',
    },

    initialize: function(options) {
      this.dirty = false;
      this.editing = false;

      // the model is a documentDom model, which holds the parsed XML
      // document and is a bit different from normal Backbone models
      this.xmlModel = options.xmlModel;
      this.xmlModel.on('change', this.setDirty, this);

      // this is the raw, unparsed XML model
      this.rawModel = options.rawModel;
      this.rawModel.on('sync', this.setClean, this);

      this.tocView = options.tocView;
      this.tocView.on('item-selected', this.editTocItem, this);

      // setup the editor controllers
      this.aceEditor = new Indigo.AceEditorController({view: this});
      this.limeEditor = new Indigo.LimeEditorController({view: this});

      this.editWithAce();
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
        return this.activeEditor.saveChanges();
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

    updateFragment: function(oldNode, newNode) {
      this.updating = true;
      try {
        this.fragment = this.xmlModel.updateFragment(oldNode, newNode);
      } finally {
        this.updating = false;
      }
    },

    editWithAce: function(e) {
      var self = this;

      this.stopEditing()
        .then(function() {
          self.$el.find('.plaintext-editor').addClass('in');
          self.$el.find('.lime-editor').removeClass('in');
          self.activeEditor = self.aceEditor;
          self.editFragment(self.fragment);
        });
    },

    editWithLime: function(e) {
      var self = this;

      this.stopEditing()
        .then(function() {
          self.$el.find('.plaintext-editor').removeClass('in');
          self.$el.find('.lime-editor').addClass('in');
          self.activeEditor = self.limeEditor;
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
        // save changes from the editor, then save the model, which resolves
        // this deferred
        var wait = $.Deferred();

        this.activeEditor
          // ask the editor to returns its contents
          .saveChanges()
          .fail(function() { wait.fail(); })
          .then(function() {
            // save the model
            self.saveModel()
              .then(function() { wait.resolve(); })
              .fail(function() { wait.fail(); });
          });

        return wait;
      } else {
        return this.saveModel();
      }
    },

    // Save the content of the raw XML model, returns a Deferred
    saveModel: function() {
      // serialize the DOM into the raw model
      this.rawModel.set('content', this.xmlModel.toXml());
      return this.rawModel.save();
    },
  });
})(window);
