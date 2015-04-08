(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // Handle the document editor, tracking changes and saving it back to the server.
  // The model is an Indigo.DocumentContent instance.
  Indigo.DocumentEditorView = Backbone.View.extend({
    el: '#content-tab',
    events: {
      'change [value=plaintext]': 'togglePlaintext',
      'change [value=lime]': 'toggleLime',
    },

    initialize: function(options) {
      var self = this;

      // setup ace editor
      this.editor = ace.edit(this.$el.find(".ace-editor")[0]);
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
    },

    editFragment: function(node) {
      // edit node, a node in the XML document
      this.fragment = node;
      this.render();
      this.$el.find('.document-sheet-container').scrollTop(0);

      var xml = this.xmlModel.toXml(node);

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
        var oldFragment = this.fragment;

        this.fragment = newFragment;
        this.render();
        this.xmlModel.updateFragment(oldFragment, newFragment);
      }
    },

    togglePlaintext: function(e) {
      this.$el.find('.plaintext-editor').addClass('in');
      this.$el.find('.lime-editor').removeClass('in');
    },

    toggleLime: function(e) {
      this.$el.find('.plaintext-editor').removeClass('in');
      this.$el.find('.lime-editor').addClass('in');
      LIME.app.resize();

      var config = {
        docMarkingLanguage: "akoma3.0",
        docType: "act",
        docLocale: this.model.get('country'),
        docLang: "eng",
      };

      LIME.XsltTransforms.transform(
        this.fragment, '/static/lime/languagesPlugins/akoma3.0/AknToXhtml.xsl', {},
        function(html) {
          config.docText = html.firstChild.outerHTML;
          LIME.app.fireEvent("loadDocument", config);
        });
    },

    updateFromLime: function() {
      var self = this;
      console.log('Fetching XML from LIME');

      LIME.app.fireEvent("translateRequest", function(xml) {
        if (self.fragment.parentElement) {
          // We're editing just a fragment.
          // LIME adds AkomaNtoso wrappers around the whole thing which we
          // need to strip.
          xml = xml.querySelector('meta').nextElementSibling;
        }
        
        self.xmlModel.updateFragment(self.fragment, xml);
      }, {
        serialize: false,
      });
    },

    render: function() {
      if (this.xsltProcessor && this.fragment) {
        var html = this.xsltProcessor.transformToFragment(this.fragment, document);
        this.$el.find('.document-sheet').html('').get(0).appendChild(html);
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
