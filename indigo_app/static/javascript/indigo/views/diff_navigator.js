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
      this.counterEl = this.el.querySelector('.diff-counter');
      this.refresh();
    },

    refresh: function() {
      const target = document.querySelector(this.el.getAttribute('data-bs-target'));
      const changedElements = target.querySelectorAll('.diff-pair, ins, del, .ins, .del');

      this.changedElements = [];

      for (let i = 0; i < changedElements.length; i++) {
        const el = changedElements[i];
        // don't go inside diff-pairs, and ignore adjacent diffs
        if (!el.parentElement.classList.contains('diff-pair') && (
          this.changedElements.length === 0 || this.changedElements[this.changedElements.length - 1] !== el.previousElementSibling)) {
          this.changedElements.push(el);
        }
      }

      this.currentElementIndex = -1;
      this.updateCounter();
    },

    prevChange: function (e) {
      // workaround for (x - 1) % 3 == -1
      if (this.currentElementIndex <= 0) {
        this.currentElementIndex = this.changedElements.length - 1;
      } else {
        this.currentElementIndex--;
      }
      if (this.currentElementIndex > -1) this.changedElements[this.currentElementIndex].scrollIntoView();
      this.updateCounter();
    },

    nextChange: function (e) {
      this.currentElementIndex = (this.currentElementIndex + 1) % this.changedElements.length;
      if (this.currentElementIndex > -1) this.changedElements[this.currentElementIndex].scrollIntoView();
      this.updateCounter();
    },

    updateCounter: function () {
      if (this.counterEl) {
        if (this.changedElements.length === 0) {
          this.counterEl.textContent = '0';
        } else {
          this.counterEl.textContent = (this.currentElementIndex + 1) + ' / ' + this.changedElements.length;
        }
      }
    },
  });
})(window);
