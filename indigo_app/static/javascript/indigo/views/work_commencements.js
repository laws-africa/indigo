(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  /**
   * Handle the work commencements display.
   */

  //TODO: Adapt Logic to backbone
  const commentView = document.querySelector("#work-commencements-view");
  const provisionCheckboxes = commentView.querySelectorAll('input[name="provisions"]');
  [...provisionCheckboxes].forEach(checkbox => {
    checkbox.addEventListener('change', (e) => handleCheckboxesChange(e.target));
  });

  function handleCheckboxesChange(currentCheckbox) {
    const parentNodeListItem = currentCheckbox.closest("li");
    const nestedListElement = parentNodeListItem.querySelector("ul");
    if (nestedListElement) {
      const listItemElements = [...nestedListElement.querySelectorAll("li")];
      listItemElements.forEach((listItemElement) => {
        const checkbox = listItemElement.querySelector(
            'input[type="checkbox"]'
        );
        if (checkbox) {
          checkbox.checked = currentCheckbox.checked;
          handleCheckboxesChange(checkbox);
        }
      });
    }
  }

  Indigo.WorkCommencementsView = Backbone.View.extend({
    el: '#work-commencements-view',
    events: {
      'click .add-commencement': 'addCommencement',
      'click .all-provisions': 'allProvisionsChanged',
      'submit .commencement-form': 'formSubmitted',
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
      if (e.namespace == 'bs.collapse') {
        e.target.parentElement.querySelector('.commencement-details').classList.remove('show');
      }
    },

    formHide: function(e) {
      // show the details
      // guard the namespace because otherwise the date selector event clashes with this one
      if (e.namespace == 'bs.collapse') {
        e.target.parentElement.querySelector('.commencement-details').classList.add('show');
      }
    },

    allProvisionsChanged: function(e) {
      $(e.target).closest('.card').find('.provisions-commenced').toggleClass('d-none', e.target.checked);
    },

    formSubmitted: function(e) {
      var form = e.target;

      // if we've selected all provisions, ensure we don't send back any selections
      if (form.elements.all_provisions.checked) {
        // we can't iterate over this in-place, so do this instead
        while (form.elements.provisions.selectedOptions.length > 0) form.elements.provisions.selectedOptions[0].selected = false;
      }
    }
  });
})(window);
