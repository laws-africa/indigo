(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // List of works for a place
  Indigo.PlaceWorksView = Backbone.View.extend({
    el: '#library',
    events: {
      'click .list-group-item a': 'linkClicked',
      'shown.bs.collapse .work-extra-detail': 'workDetailToggled',
      'hidden.bs.collapse .work-extra-detail': 'workDetailToggled',
    },

    initialize: function() {
      this.drawCharts();
    },

    drawCharts: function() {
      this.drawActivityChart();
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

    drawActivityChart: function() {
      var canvas = document.getElementById('activity-chart'),
          ctx = canvas.getContext('2d'),
          data = JSON.parse(canvas.getAttribute('data-values'));

      data = _.map(data, function(pair) { return {t: pair[0], y: pair[1]}; });

      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data,
          datasets: [{
            label: "Actions",
            data: data,
            borderWidth: 0,
            backgroundColor: 'rgba(67, 159, 120, 1)',
          }]
        },
        options: {
          maintainAspectRatio: false,
          legend: {display: false},
          scales: {
            xAxes: [{
              type: 'time',
              distribution: 'linear',
              time: {
                minUnit: 'day',
              },
              ticks: {
                source: 'auto',
                autoSkip: true,
              }
            }],
            yAxes: [{
              display: true,
              ticks: {
                min: 0,
                beginAtZero: true,
              },
            }],
          }
        }
      });
    },

  });
})(window);
