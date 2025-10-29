(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handle the work commencements display.
   */
  Indigo.WorkCommencementsView = Backbone.View.extend({
    el: '#work-commencements-view',
    events: {
      'click .all-provisions': 'allProvisionsChanged',
      'change .commencement-form input[name="provisions"]' : 'handleCheckboxesChange',
      'click .commencement-form .expand-collapse-button' : 'onExpandCollapseClick',
      'change .commencement-form input[name="provisions_select_all"]' : "onSelectAll",
    },

    initialize: function() {
    },

    allProvisionsChanged: function(e) {
      $(e.target).closest('.card').find('.provisions-commenced').toggleClass('d-none', e.target.checked);
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

    handleCheckboxesChange(e) {
      const ulElement = e.target.closest("li").querySelector('ul');
      //There may not always be a nested ul
      if (ulElement) {
        for (const checkBox of ulElement.querySelectorAll("input[name='provisions']")) {
          checkBox.checked = e.target.checked;
        }
      }
    },

    onSelectAll: function (e) {
      for (const checkbox of e.target.closest("div[class='provisions-wrapper']").querySelectorAll(".commencement-form input[name='provisions']")) {
        checkbox.checked = e.target.checked;
      }
    }
  });
})(window);
