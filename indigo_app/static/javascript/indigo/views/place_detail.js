(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // List of works for a place
  Indigo.PlaceDetailView = Backbone.View.extend({
    el: '.main-content',

    initialize: function() {
      this.drawActivityChart();
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
