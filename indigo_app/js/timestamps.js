import { DateTime } from 'luxon';
import { Tooltip } from 'bootstrap';
export function relativeTimestamps (root) {
  // show timestamps as relative times
  const elements = (root || document).querySelectorAll('.time-ago[data-timestamp]');

  elements.forEach((el) => {
    const ts = DateTime.fromISO(el.getAttribute('data-timestamp'));
    el.innerText = ts.toRelative();

    if (!el.getAttribute('title')) {
      el.setAttribute('title', ts.toLocaleString(DateTime.DATETIME_FULL));
      el.dataset.bsToggle = 'tooltip'; // Add this line to set the tooltip toggle
      el.dataset.bsPlacement = 'top'; // You can adjust the placement as needed
    }
  });

  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new Tooltip(tooltipTriggerEl);
  });
}

function tickTock () {
  relativeTimestamps();
  window.setTimeout(tickTock, 60 * 1000);
}

tickTock();
