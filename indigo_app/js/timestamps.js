import { DateTime } from 'luxon';

export function relativeTimestamps (root) {
  // show timestamps as relative times
  for (const el of (root || document).querySelectorAll('.time-ago[data-timestamp]')) {
    const ts = DateTime.fromISO(el.getAttribute('data-timestamp'));

    el.innerText = ts.toRelative();
    if (!el.getAttribute('title')) {
      el.setAttribute('title', ts.toLocaleString(DateTime.DATETIME_FULL));
      $(el).tooltip();
    }
  }
}

function tickTock () {
  relativeTimestamps();
  window.setTimeout(tickTock, 60 * 1000);
}

tickTock();
