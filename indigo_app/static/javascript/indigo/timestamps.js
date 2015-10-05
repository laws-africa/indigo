$(function() {
  Indigo.relativeTimestamps = function() {
    // show timestamps as relative times
    $('.time-ago[data-timestamp]').each(function() {
      var $this = $(this),
          ts = moment($this.data('timestamp'));

      $this.html(ts.fromNow());

      if (!$this.attr('title')) {
        $this
          .attr('title', ts.format('LL [at] LT'))
          .tooltip();
      }
    });
  };

  function tickTock() {
    Indigo.relativeTimestamps();
    window.setTimeout(tickTock, 60*1000);
  }

  tickTock();
});
