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
      this.drawWorksByYearChart();
      this.drawAmendmentsByYearChart();
      this.drawWorksByTypeChart();
      this.drawCompletenessChart();
      this.drawWorksChart();
      this.drawExpressionsChart();
      this.drawActivityChart();
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
            borderWidth: 0,
            backgroundColor: 'rgba(67, 159, 120, 1)',
          }]
        },
        options: {
          maintainAspectRatio: false,
          legend: {display: false},
          scales: {
            yAxes: [{
              ticks: {
                precision: 0,
                beginAtZero: true,
              },
            }],
          },
        }
      });
    },

    drawAmendmentsByYearChart: function() {
      var canvas = document.getElementById('amendments_by_year-chart'),
          ctx = canvas.getContext('2d'),
          data = JSON.parse(canvas.getAttribute('data-values'));

      var values = _.map(data, function(pair) { return pair[1]; });
      var labels = _.map(data, function(pair) { return pair[0]; });

      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Amendments',
            data: values,
            borderWidth: 0,
            backgroundColor: 'rgba(67, 159, 120, 1)',
          }]
        },
        options: {
          maintainAspectRatio: false,
          legend: {display: false},
          scales: {
            yAxes: [{
              ticks: {
                precision: 0,
                beginAtZero: true,
              },
            }],
          },
        }
      });
    },

    drawWorksByTypeChart: function() {
      var canvas = document.getElementById('works_by_type-chart'),
          ctx = canvas.getContext('2d'),
          data = JSON.parse(canvas.getAttribute('data-values'));

      var values = _.map(data, function(pair) { return pair[1]; });
      var labels = _.map(data, function(pair) { return pair[0]; });

      new Chart(ctx, {
        type: 'horizontalBar',
        data: {
          labels: labels,
          datasets: [{
            data: values,
            borderWidth: 0,
            backgroundColor: 'rgba(67, 159, 120, 1)',
          }]
        },
        options: {
          maintainAspectRatio: false,
          legend: {display: false},
          scales: {
            yAxes: [{
              ticks: {
                precision: 0,
                beginAtZero: true,
              },
            }],
          },
        }
      });
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
    }
  });
})(window);
