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
      this.documentContent.on('change:dom', () => {
        // if the fragment has been swapped out, don't use a stale fragment; our parent will
        // call editFragment() to update our fragment
        if (this.visible && this.fragment && this.fragment.ownerDocument === this.documentContent.xmlDocument) {
          this.render();
        }
      });
    },

    editFragment: function(fragment) {
      this.fragment = fragment;
      if (this.visible) {
        this.render();
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
      // pretty-print the xml
      const xml = prettyPrintXml(Indigo.toXml(this.fragment));
      if (this.editor.getValue() !== xml) {
        const posn = this.editor.getPosition();

        // ignore the onDidChangeModelContent event triggered by setValue
        this.updating = true;
        this.editor.setValue(xml);
        this.updating = false;

        this.editor.setPosition(posn);
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

        /*
        * Because we are resizing the editor by result of `this.editor.layout()` inside the callback of resize observer of that
        * editor, an infinite loop might occur, since we are watching size changes, then triggering a size. The browser
        * will take action to counter with results in the error ResizeObserver loop limit exceeded.
        * We can completely eliminate this by suspending the observation and restart on the next animation frame,
        * but only if the element resized while the handler was executing
        * */

        const resizeObserver = new ResizeObserver(() => {
          const initialSize = this.editor.getContainerDomNode().getBoundingClientRect();
          // Potential resizing happens
          this.editor.layout();
          // Get new size
          const newSize = this.editor.getContainerDomNode().getBoundingClientRect();

          if (
              initialSize.width != newSize.width ||
              initialSize.height != newSize.height
          ) {
            resizeObserver.unobserve(this.editor.getContainerDomNode());
            window.requestAnimationFrame(() => {
              resizeObserver.observe(this.editor.getContainerDomNode());
            });
          }

        });
        resizeObserver.observe(this.editor.getContainerDomNode());

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

      this.parent.updateFragment(this.parent.fragment, [newFragment]);
    },

  });
})(window);
