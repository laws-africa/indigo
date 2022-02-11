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
      'click .add-commencement': 'addCommencement',
      'click .all-provisions': 'allProvisionsChanged',
      'submit .commencement-form': 'formSubmitted',
      'change .commencement-form input[name="provisions"]' : 'handleCheckboxesChange',
      'click .commencement-form .expand-collapse-button' : 'onExpandCollapseClick',
      'change .commencement-form input[name="select-all"]' : "onSelectAll",
    },

    initialize: function() {
      this.model = new Indigo.Work(Indigo.Preloads.work);

      this.$('.commencement-form').on('show.bs.collapse', _.bind(this.formShow, this));
      this.$('.commencement-form').on('hide.bs.collapse', _.bind(this.formHide, this));
    },

    addCommencement: function(e) {
      e.preventDefault();

      var chooser = new Indigo.WorkChooserView({
            country: this.model.get('country'),
            locality: this.model.get('locality') || "-",
          }),
          form = document.getElementById('new-commencement-form'),
          self = this;

      chooser.showModal().done(function(chosen) {
        if (chosen) {
          form.elements.date.value = chosen.get('commencement_date') || chosen.get('publication_date');
          form.elements.commencing_work.value = chosen.get('id');
          form.submit();
        }
      });
    },

    formShow: function(e) {
      // hide the details
      // guard the namespace because otherwise the date selector event clashes with this one
      if (e.namespace == 'bs.collapse' && e.target.classList.contains('commencement-form')) {
        e.target.parentElement.querySelector('.commencement-details').classList.remove('show');
      }
    },

    formHide: function(e) {
      // show the details
      // guard the namespace because otherwise the date selector event clashes with this one
      if (e.namespace == 'bs.collapse' && e.target.classList.contains('commencement-form')) {
        e.target.parentElement.querySelector('.commencement-details').classList.add('show');
      }
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

    formSubmitted: function(e) {
      var form = e.target;

      // if we've selected all provisions, ensure we don't send back any selections
      if (form.elements.all_provisions.checked) {
        [...form.elements.provisions].forEach(function(provision) {
          provision.checked = false;
        })
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
      for (const checkbox of document.querySelectorAll(".commencement-form input[name='provisions']")) {
        checkbox.checked = e.target.checked;
      }
    }
  });
})(window);
