import { DateTime } from 'luxon';
export function relativeTimestamps (root) {
  // show timestamps as relative times
  const elements = (root || document).querySelectorAll('.time-ago[data-timestamp]');

  elements.forEach((el) => {
    const ts = DateTime.fromISO(el.getAttribute('data-timestamp'));
    el.innerText = ts.toRelative();

    if (!el.getAttribute('title')) {
      el.dataset.bsToggle = 'tooltip';
      el.dataset.bsPlacement = 'top';
      el.dataset.bsTitle = ts.toLocaleString(DateTime.DATETIME_FULL);
    }
  });
}

function tickTock () {
  relativeTimestamps();
  window.setTimeout(tickTock, 60 * 1000);
}

tickTock();
