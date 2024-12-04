(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handle the document provisions display.
   * TODO: nuke this whole file when we use the document ToC instead
   */
  Indigo.ChooseDocumentProvisionView = Backbone.View.extend({
    el: '#document-provisions-view',
    events: {
      'click .provision-form .expand-collapse-button' : 'onExpandCollapseClick',
    },

    onExpandCollapseClick: function(e) {
      e.stopPropagation();
      const button = e.currentTarget;
      const parent = button.closest('li');
      button.classList.toggle('expanded');

      if (parent) {
        const collapseElement = $(parent.querySelector('.collapse'));
        if(collapseElement.length) {
          collapseElement.collapse('toggle');
        }
      }
    },
  });
})(window);
