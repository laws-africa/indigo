(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // Handle the document editor, tracking changes and saving it back to the server.
  // The model is an Indigo.DocumentBody instance.
  Indigo.DocumentEditorView = Backbone.View.extend({
    el: '#content-tab',

    initialize: function(options) {
      var self = this;

      // setup ace editor
      this.editor = ace.edit(this.$el.find(".ace-editor")[0]);
      this.editor.setTheme("ace/theme/monokai");
      this.editor.getSession().setMode("ace/mode/xml");
      this.editor.setValue();
      this.editor.$blockScrolling = Infinity;
      this.editor.on('change', _.debounce(_.bind(this.updateDocumentBody, this), 500));

      // setup renderer
      var xsltProcessor = new XSLTProcessor();
      $.get('/static/xsl/act.xsl')
        .then(function(xml) {
          xsltProcessor.importStylesheet(xml);
          self.xsltProcessor = xsltProcessor;
          self.render();
        });

      this.dirty = false;
      this.model.on('change', this.updateEditor, this);
      this.model.on('change', this.parseXml, this);
      this.model.on('change', this.setDirty, this);
      this.model.on('sync', this.setClean, this);

      this.tocView = options.tocView;
      this.tocView.on('item-clicked', this.editFragment, this);

      this.fragment = this.model.xmlDocument;
    },

    parseXml: function() {
      try {
        this.model.xmlDocument = $.parseXML(this.model.get('body'));
        this.render();
      } catch(e) {
        console.log(e);
      }
    },

    editFragment: function(node) {
      // edit node, a node in the XML document
      this.fragment = node;
      this.render();
      this.$el.find('.document-sheet-container').scrollTop(0);
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
      // TODO: validation

      // don't do anything if it hasn't changed
      if (!this.dirty) {
        return $.Deferred().resolve();
      }

      return this.model.save();
    },

    updateEditor: function(model, options) {
      // update the editor with new content from the model,
      // unless this new content already comes from the editor
      if (!options.fromEditor) this.editor.setValue(this.model.get('body'));
    },

    updateDocumentBody: function() {
      // update the document content from the editor's version
      console.log('new body content');
      this.model.set(
        {body: this.editor.getValue()},
        {fromEditor: true}); // prevent infinite loop
    },
  });
})(window);
