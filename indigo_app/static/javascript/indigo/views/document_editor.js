(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // The AceEditorController manages the interaction between
  // the ace-based editor, the model, and the document editor view.
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
      var xsltProcessor = new XSLTProcessor();
      $.get('/static/xsl/act.xsl')
        .then(function(xml) {
          xsltProcessor.importStylesheet(xml);
          self.xsltProcessor = xsltProcessor;
        });
    },

    editFragment: function(node) {
      // edit node, a node in the XML document
      this.render();
      this.view.$el.find('.document-sheet-container').scrollTop(0);

      var xml = this.view.xmlModel.toXml(node);

      this.editor.removeListener('change', this.onEditorChange);
      this.editor.setValue(xml);
      this.editor.on('change', this.onEditorChange);
    },

    editorChanged: function() {
      if (!this.updating) {
        // update the fragment content from the editor's version
        console.log('Parsing changes to XML');

        // TODO: handle errors here
        var newFragment = $.parseXML(this.editor.getValue()).documentElement;
        var oldFragment = this.view.fragment;

        this.view.fragment = newFragment;
        this.render();
        this.view.xmlModel.updateFragment(oldFragment, newFragment);
      }
    },

    render: function() {
      if (this.xsltProcessor && this.view.fragment) {
        var html = this.xsltProcessor.transformToFragment(this.view.fragment, document);
        this.view.$el.find('.document-sheet').html('').get(0).appendChild(html);
      }
    },

  });

  // The LimeEditorController manages the interaction between
  // the LIME-based editor, the model, and the document editor view.
  Indigo.LimeEditorController = function(options) {
    this.initialize.apply(this, arguments);
  };
  _.extend(Indigo.LimeEditorController.prototype, Backbone.Events, {
    initialize: function(options) {
      this.view = options.view;
    },

    editFragment: function(node) {
      LIME.app.resize();

      var config = {
        docMarkingLanguage: "akoma3.0",
        docType: "act",
        docLocale: this.view.model.get('country'),
        docLang: "eng",
      };

      LIME.XsltTransforms.transform(
        node,
        '/static/lime/languagesPlugins/akoma3.0/AknToXhtml.xsl',
        {},
        function(html) {
          config.docText = html.firstChild.outerHTML;
          LIME.app.fireEvent("loadDocument", config);
        }
      );
    },

    updateFromLime: function() {
      var view = this.view;
      console.log('Fetching XML from LIME');

      LIME.app.fireEvent("translateRequest", function(xml) {
        if (view.fragment.parentElement) {
          // We're editing just a fragment.
          // LIME adds AkomaNtoso wrappers around the whole thing which we
          // need to strip.
          xml = xml.querySelector('meta').nextElementSibling;
        }
        
        view.xmlModel.updateFragment(view.fragment, xml);
      }, {
        serialize: false,
      });
    },
  });


  // Handle the document editor, tracking changes and saving it back to the server.
  // The model is an Indigo.DocumentContent instance.
  Indigo.DocumentEditorView = Backbone.View.extend({
    el: '#content-tab',
    events: {
      'change [value=plaintext]': 'editWithAce',
      'change [value=lime]': 'editWithLime',
    },

    initialize: function(options) {
      this.dirty = false;

      // the model is a documentDom model, which holds the parsed XML
      // document and is a bit different from normal Backbone models
      this.xmlModel = options.xmlModel;
      this.xmlModel.on('change', this.setDirty, this);

      // this is the raw, unparsed XML model
      this.rawModel = options.rawModel;
      this.rawModel.on('sync', this.setClean, this);

      this.tocView = options.tocView;
      this.tocView.on('item-selected', this.editFragment, this);

      // setup the editor controllers
      this.aceEditor = new Indigo.AceEditorController({view: this});
      this.limeEditor = new Indigo.LimeEditorController({view: this});

      this.editWithAce();
    },

    editFragment: function(node) {
      this.fragment = node;
      this.activeEditor.editFragment(node);
    },

    editWithAce: function(e) {
      this.$el.find('.plaintext-editor').addClass('in');
      this.$el.find('.lime-editor').removeClass('in');
      this.activeEditor = this.aceEditor;
      if (this.fragment) {
        this.activeEditor.editFragment(this.fragment);
      }
    },

    editWithLime: function(e) {
      this.$el.find('.plaintext-editor').removeClass('in');
      this.$el.find('.lime-editor').addClass('in');
      this.activeEditor = this.limeEditor;
      if (this.fragment) {
        this.activeEditor.editFragment(this.fragment);
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

    save: function() {
      // don't do anything if it hasn't changed
      if (!this.dirty) {
        return $.Deferred().resolve();
      }

      // serialize the DOM into the raw model
      this.rawModel.set('body', this.xmlModel.toXml());
      return this.rawModel.save();
    },
  });
})(window);
