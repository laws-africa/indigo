// show timestamps as relative times
function formatTimestamps() {
  $('.time-ago[data-timestamp]').each(function() {
    var $this = $(this),
        ts = moment($this.data('timestamp'));

    $this
      .attr('title', ts.format('LL [at] LT'))
      .tooltip()
      .html(ts.fromNow());
  });
}

$(function() {
  formatTimestamps();
});
