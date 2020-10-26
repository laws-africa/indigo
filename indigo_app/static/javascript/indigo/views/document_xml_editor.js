(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // The XMLEditorView manages the source (xml) editor component.
  Indigo.XMLEditorView = Backbone.View.extend({
    el: '.document-xml-editor',

    initialize: function(options) {
      this.fragment = null;
      this.updating = false;
      this.parent = options.parent;
      this.documentContent = options.documentContent;
      this.documentContent.on('change:dom', this.render.bind(this));
    },

    editFragment: function(fragment) {
      if (!this.updating) {
        this.fragment = fragment;
        if (this.visible) {
          this.render();
        }
      }
    },

    show: function() {
      this.visible = true;
      this.setupXmlEditor();
      this.render();
    },

    hide: function() {
      this.visible = false;
    },

    render: function() {
      if (this.visible) {
        // pretty-print the xml
        const xml = prettyPrintXml(Indigo.toXml(this.fragment));
        this.updating = true;
        this.editor.setValue(xml);
        this.updating = false;
        this.editor.layout();
      }
    },

    setupXmlEditor: function() {
      if (!this.editor) {
        this.editor = window.monaco.editor.create(this.el.querySelector('.monaco-editor'), {
          codeLens: false,
          detectIndentation: false,
          foldingStrategy: 'indentation',
          language: 'xml',
          lineDecorationsWidth: 0,
          lineNumbersMinChars: 3,
          roundedSelection: false,
          scrollBeyondLastLine: false,
          showFoldingControls: 'always',
          tabSize: 2,
          wordWrap: 'on',
          theme: 'vs',
          wrappingIndent: 'same',
        });

        new ResizeObserver(() => { this.editor.layout(); }).observe(this.editor.getContainerDomNode());
        const onEditorChange = _.debounce(_.bind(this.editorChanged, this), 500);
        this.editor.onDidChangeModelContent(() => {
          if (!this.updating) onEditorChange();
        });
      }
    },

    editorChanged: function() {
      // save the contents of the XML editor
      let newFragment;
      console.log('Parsing changes to XML');

      try {
        newFragment = $.parseXML(this.editor.getValue()).documentElement;
      } catch(err) {
        // squash errors
        console.log(err);
        return;
      }

      this.updating = true;
      try {
        this.parent.updateFragment(this.parent.fragment, [newFragment]);
      } finally {
        this.updating = false;
      }
    },

  });
})(window);
