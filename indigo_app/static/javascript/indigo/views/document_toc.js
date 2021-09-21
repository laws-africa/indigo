(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // This view shows the table-of-contents of the document and handles clicks
  Indigo.DocumentTOCView = Backbone.View.extend({
    el: "#toc",

    initialize: function(options) {
      this.issues = options.document.issues;
      this.registeredComp = window.globalVue.options.components.DocumentTOCView;
      this.targetMountElement = document.getElementById("DocumentTOCView");
      this.selection = new Backbone.Model({
        index: -1
      });

      this.compInstance = null;
      if (this.registeredComp && this.targetMountElement) {
        this.render();
      }
    },
    render: function() {
      var CompClass = window.globalVue.extend(this.registeredComp);
      var compInstance = new CompClass({
        propsData: { backBoneContext: this }
      });
      compInstance.$mount(this.targetMountElement);
      this.compInstance = compInstance;
    },

    selectItem: function(i, force) {
      if (this.compInstance) {
        this.compInstance.selectItem(i, force);
      }
    }
  });
})(window);
