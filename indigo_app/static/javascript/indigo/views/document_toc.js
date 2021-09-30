(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // This view shows the table-of-contents of the document and handles clicks
  Indigo.DocumentTOCView = Backbone.View.extend({
    el: "#toc",

    initialize: function(options) {
      this.issues = options.document.issues;
      this.listenTo(this.issues, 'reset change add remove', this.issuesChanged);

      this.registeredComp = indigoApp.Vue.options.components.DocumentTOCView;
      this.targetMountElement = document.getElementById("DocumentTOCView");
      this.selection = new Backbone.Model({
        index: -1
      });

      this.compInstance = null;
      if (this.registeredComp && this.targetMountElement) {
        var CompClass = indigoApp.Vue.extend(this.registeredComp);
        var compInstance = new CompClass({
          propsData: {
            selection: this.selection,
            model: this.model,
            issues: this.issues
          }
        });
        compInstance.$mount(this.targetMountElement);
        this.compInstance = compInstance;
      }
    },

    issuesChanged: function () {
      // force vue to realise the issues list has changed
      this.compInstance.issues = [];
      this.compInstance.issues = this.issues;
    },

    selectItem: function(i, force) {
      if (this.compInstance) this.compInstance.selectItem(i, force);
    },

    selectItemById: function(itemId) {
      if (this.compInstance) this.compInstance.selectItemById(itemId);
    }
  });
})(window);
