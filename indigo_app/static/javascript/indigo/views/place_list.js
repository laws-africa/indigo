(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.PlaceListView = Backbone.View.extend({
    el: '#main-container',

    initialize: function() {
      this.drawCharts();
    },

    drawCharts: function() {
      this.drawActivityCharts();
    },

    drawTimeSeriesChart: function(canvas, data, label) {
      var ctx = canvas.getContext('2d');

      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data,
          datasets: [{
            label: label,
            data: data,
            borderWidth: 2,
            lineTension: 0,
            pointRadius: 0,
            backgroundColor: 'rgba(67, 159, 120, 0.2)',
            borderColor: 'rgba(67, 159, 120, 1)',
            fill: false,
          }]
        },
        options: {
          maintainAspectRatio: false,
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
            xAxes: [{
              type: 'time',
              distribution: 'series',
              time: {
                minUnit: 'day',
              },
              ticks: {
                source: 'data',
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

    drawActivityCharts: function() {
      var self = this;
      $('.place-activity-chart').each(function(i, canvas) {
        self.drawActivityChart(e);
      });
    },

    drawActivityChart: function(canvas) {
      var data = JSON.parse(canvas.getAttribute('data-values'));

      data = _.map(data, function(pair) { return {t: pair[0], y: pair[1]}; });
      this.drawTimeSeriesChart(canvas, data, 'Works');
    },
  });
})(window);
