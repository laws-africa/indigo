(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handle the revisions of a document.
   */
  Indigo.DiffNavigator = Backbone.View.extend({
    events: {
      'click .prev-change-btn': 'prevChange',
      'click .next-change-btn': 'nextChange',
    },

    initialize: function (options) {
      this.refresh();
    },

    refresh: function() {
      this.changedElements = $(this.el.getAttribute('data-bs-target')).find('ins, del, .ins, .del');
      this.currentElementIndex = -1;
    },

    prevChange: function (e) {
      // workaround for (x - 1) % 3 == -1
      if (this.currentElementIndex <= 0) {
        this.currentElementIndex = this.changedElements.length - 1;
      } else {
        this.currentElementIndex--;
      }
      if (this.currentElementIndex > -1) this.changedElements[this.currentElementIndex].scrollIntoView();
    },

    nextChange: function (e) {
      this.currentElementIndex = (this.currentElementIndex + 1) % this.changedElements.length;
      if (this.currentElementIndex > -1) this.changedElements[this.currentElementIndex].scrollIntoView();
    }
  });
})(window);
