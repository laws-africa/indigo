(function(exports) {
  "use strict";

  if (!exports.Indigo) exports.Indigo = {};
  Indigo = exports.Indigo;

  Indigo.PlaceMetricsView = Backbone.View.extend({
    el: '#main-container',

    initialize: function() {
      this.drawCharts();
    },

    drawCharts: function() {
      this.drawCompletenessChart();
      this.drawWorksChart();
      this.drawExpressionsChart();
      this.drawWorksByYearChart();
    },

    drawTimeSeriesChart: function(canvas, data, label) {
      var ctx = canvas.getContext('2d');

      new Chart(ctx, {
        type: 'line',
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

    drawWorksChart: function() {
      var canvas = document.getElementById('n_works_history-chart'),
          data = JSON.parse(canvas.getAttribute('data-values'));

      data = _.map(data, function(pair) { return {t: pair[0], y: pair[1]}; });
      this.drawTimeSeriesChart(canvas, data, 'Works');
    },

    drawExpressionsChart: function() {
      var canvas = document.getElementById('n_expressions_history-chart'),
          data = JSON.parse(canvas.getAttribute('data-values'));

      data = _.map(data, function(pair) { return {t: pair[0], y: pair[1]}; });
      this.drawTimeSeriesChart(canvas, data, 'Expressions');
    },

    drawCompletenessChart: function() {
        var canvas = document.getElementById('completeness-chart'),
            ctx = canvas.getContext('2d'),
            data = JSON.parse(canvas.getAttribute('data-values'));

      data = _.map(data, function(pair) { return {t: pair[0], y: pair[1]}; });

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
              xAxes: [{
                type: 'time',
                time: {
                  minUnit: 'day',
                },
              }],
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

    drawWorksByYearChart: function() {
      var canvas = document.getElementById('works_by_year-chart'),
          ctx = canvas.getContext('2d'),
          data = JSON.parse(canvas.getAttribute('data-values'));

      var values = _.map(data, function(pair) { return pair[1]; });
      var labels = _.map(data, function(pair) { return pair[0]; });

      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Works',
            data: values,
            borderWidth: 2,
            backgroundColor: 'rgba(67, 159, 120, 0.2)',
            borderColor: 'rgba(67, 159, 120, 1)',
          }]
        },
        options: {
          maintainAspectRatio: false,
          legend: {display: false},
        }
      });
    },
  });
})(window);
