(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  // List of works for a place
  Indigo.PlaceDetailView = Backbone.View.extend({
    el: '.main-content',

    initialize: function() {
      this.drawActivityChart();
      this.drawCompletenessChart();
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

    drawCompletenessChart: function() {
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
    },

  });
})(window);
