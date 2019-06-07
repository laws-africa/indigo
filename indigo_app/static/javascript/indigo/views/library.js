(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // displays in the library div
  Indigo.LibraryView = Backbone.View.extend({
    el: '#library',
    template: '#search-results-template',
    events: {
      'click .toggle-docs': 'toggleDocuments',
      'click .list-group-item a': 'linkClicked',
      'shown.bs.collapse .work-extra-detail': 'workDetailToggled',
      'hidden.bs.collapse .work-extra-detail': 'workDetailToggled',
    },

    initialize: function() {
      this.template = Handlebars.compile($(this.template).html());

      // the filter view does all the hard work of actually fetching and
      // filtering the documents
      //this.filterView = new Indigo.LibraryFilterView();
      //this.filterView.on('change', this.render, this);
      //this.filterView.trigger('change');
      this.drawCharts();
    },

    linkClicked: function(e) {
      // don't bubble to avoid collapsing the container unnecessarily
      e.stopPropagation();
    },

    workDetailToggled: function(e) {
      var row = e.target.parentNode,
          $icon = $(row).find('.collapse-indicator'),
          opened = $(e.target).hasClass('show');

      $icon.toggleClass('fa-caret-right', !opened)
           .toggleClass('fa-caret-down', opened);
    },

    render: function() {
      var works = this.filterView.filteredWorks,
          docs = this.filterView.filteredDocs;

      // tie works and docs together
      works = _.map(works, function(work) {
        var currentUserId = Indigo.user.get('id');

        work = work.toJSON();
        work.n_annotations = 0;

        var work_docs = _.map(docs[work.id] || [], function(doc) {
          return doc.toJSON();
        });

        // distinct languages
        work.n_languages = _.unique(_.map(work_docs, function(doc) {
          return doc.language;
        })).length;

        // count expression dates
        work.n_expressions = _.unique(_.map(work_docs, function(doc) {
          return doc.expression_date;
        })).length;

        // number of drafts
        work.drafts_v_published = _.countBy(work_docs, function(doc) {
          return doc.draft ? 'n_drafts': 'n_published';
        });

        // total number of docs
        work.n_docs = work_docs.length;
        work.n_docs_singular = work_docs.length == 1;

        work.n_published = work.drafts_v_published.n_published || 0;
        work.n_drafts = work.drafts_v_published.n_drafts || 0;
        work.n_docs_drafts_singular = work.n_drafts === 1;
        work.n_amendments = (Indigo.Preloads.work_n_amendments[work.id] || {}).n_amendments || 0;
        work.no_children = work.n_docs === 0 && work.n_amendments === 0;
        work.n_expected_docs = (1 + work.n_amendments) * (work.n_languages || 1);

        // get a ratio of drafts vs total docs for sorting
        if (work.n_docs !== 0) {
          work.drafts_ratio = 100 * (work.n_drafts / work.n_expected_docs);
          work.pub_ratio = 100 * (work.n_published / work.n_expected_docs);
        } else {
          work.drafts_ratio = 0;
          work.pub_ratio = 0;
        }

        // add work to list of docs and order by recency
        var work_and_docs = work_docs.concat([work]);

        var most_recently_updated = work_and_docs.sort(function(a, b) {
          return -a.updated_at.localeCompare(b.updated_at);
        })[0];

        work.updated_at = most_recently_updated.updated_at;

        // current user's name -> 'you'
        if (most_recently_updated.updated_by_user && most_recently_updated.updated_by_user.id == currentUserId) {
          most_recently_updated.updated_by_user.display_name = 'you';
        }

        work.most_recent_updated_by = most_recently_updated.updated_by_user;

        work_docs.forEach(function(work_doc) {
          if (work_doc.updated_by_user && work_doc.updated_by_user.id === currentUserId) {
            work_doc.updated_by_user.display_name = 'you';
          }

          // number of annotations / comments on each doc and work
          work_doc.n_annotations = (Indigo.Preloads.document_annotations[work_doc.id] || {}).n_annotations || 0;
          work.n_annotations += work_doc.n_annotations;

          // task stats
          work_doc.task_stats = Indigo.Preloads.document_tasks[work_doc.id] || {};
          work_doc.task_stats.n_active_tasks = (work_doc.task_stats.n_open_tasks || 0) + (work_doc.task_stats.n_pending_review_tasks || 0);
          work_doc.task_stats.pending_task_ratio = 100 * ((work_doc.task_stats.n_pending_review_tasks || 0) / work_doc.task_stats.n_active_tasks) || 0;
          work_doc.task_stats.open_task_ratio = 100 * ((work_doc.task_stats.n_open_tasks || 0) / work_doc.task_stats.n_active_tasks) || 0;
        });

        work.task_stats = Indigo.Preloads.work_tasks[work.id] || {};
        work.task_stats.n_active_tasks = (work.task_stats.n_open_tasks || 0) + (work.task_stats.n_pending_review_tasks || 0);
        work.task_stats.pending_task_ratio = 100 * ((work.task_stats.n_pending_review_tasks || 0) / work.task_stats.n_active_tasks) || 0;
        work.task_stats.open_task_ratio = 100 * ((work.task_stats.n_open_tasks || 0) / work.task_stats.n_active_tasks) || 0;

        // docs for this work
        work.work_docs = _.sortBy(work_docs, 'expression_date');
        work.work_docs.reverse();

        return work;
      });

      works = _.sortBy(works, this.filterView.sortField);
      if (this.filterView.sortDesc) works.reverse();

      this.$el.html(this.template({
        count: works.length,
        works: works,
      }));

      this.$el.find('[title]').tooltip({
        container: 'body',
        placement: 'auto'
      });

      Indigo.relativeTimestamps();
    },

    drawCharts: function() {
        var canvas = document.getElementById('completeness-chart'),
            ctx = canvas.getContext('2d'),
            data = _.map(canvas.getAttribute('data-values').split(','), function(i) { return parseInt(i); });

        new Chart(ctx, {
          type: 'line',
          data: {
            labels: data,
            datasets: [{
              label: 'Completeness',
              data: data,
              backgroundColor: 'rgba(67, 159, 120, 0.2)',
              borderColor: 'rgba(67, 159, 120, 1)',
              borderWidth: 2,
              fill: 'start',
            }]
          },
          options: {
            maintainAspectRatio: false,
            tooltips: {
              callbacks: {
                title: function(items, data) { return items[0].value + '%'; },
                label: function(item, data) { return; },
                beforeLabel: function(item, data) { return; },
              },
            },
            layout: {
              padding: {
                top: 2,
                left: 2,
                right: 2,
                bottom: 1,
              }
            },
            legend: {display: false},
            elements: {
              line: {
                tension: 0.4,
              },
              point: {
                radius: 0,
              },
            },
            scales: {
              xAxes: [{display: false}],
              yAxes: [{
                display: false,
                ticks: {
                  min: 0,
                  max: 100,
                  beginAtZero: true,
                }
              }]
            }
          }
        });
    }
  });
})(window);
