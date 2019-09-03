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
            borderWidth: 0,
            backgroundColor: 'rgba(67, 159, 120, 0.2)',
          }]
        },
        options: {
          maintainAspectRatio: false,
          legend: {display: false},
          tooltips: {enabled: false},
          scales: {
            xAxes: [{
              display: false,
            }],
            yAxes: [{
              display: false,
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
        self.drawActivityChart(canvas);
      });
    },

    drawActivityChart: function(canvas) {
      var data = JSON.parse(canvas.getAttribute('data-values'));

      data = _.map(data, function(pair) { return {t: pair[0], y: pair[1]}; });
      this.drawTimeSeriesChart(canvas, data, 'Activity');
    },
  });
})(window);
