export class VSplitter {
  constructor (splitter) {
    this.splitter = splitter;
    this.container = splitter.parentElement;
    this.leftPane = splitter.previousElementSibling;
    this.rightPane = splitter.nextElementSibling;
    this.isDragging = false;

    this.splitter.addEventListener('mousedown', (e) => this.onMouseDown(e));
    this.mouseUp = this.onMouseUp.bind(this);
    this.mouseMove = this.onMouseMove.bind(this);

    if (this.splitter.id) {
      this.storageKey = `splitter-${this.splitter.id}`;
      this.loadState();
    } else {
      this.storageKey = null;
    }
  }

  loadState () {
    let width = window.localStorage.getItem(this.storageKey);
    if (width) {
      try {
        width = Math.max(10, Math.min(90, parseFloat(width)));
        this.leftPane.style.flexBasis = `${width}%`;
        this.rightPane.style.flexBasis = `${100.0 - width}%`;
      } catch {
        window.localStorage.removeItem(this.storageKey);
      }
    }
  }

  saveState (width) {
    if (this.storageKey) {
      window.localStorage.setItem(`splitter-${this.splitter.id}`, width.toString());
    }
  }

  onMouseDown (e) {
    this.isDragging = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    document.addEventListener('mouseup', this.mouseUp);
    document.addEventListener('mousemove', this.mouseMove);
  }

  onMouseUp (e) {
    if (this.isDragging) {
      this.isDragging = false;
      document.body.style.cursor = 'default';
      document.body.style.userSelect = null;
      document.removeEventListener('mouseup', this.mouseUp);
      document.removeEventListener('mousemove', this.mouseMove);
    }
  }

  onMouseMove (e) {
    if (!this.isDragging) return;

    // Calculate new widths
    const containerOffsetLeft = this.container.getBoundingClientRect().left;
    const pointerRelativeXpos = e.clientX - containerOffsetLeft;
    const containerWidth = this.container.clientWidth;
    const splitterWidth = this.splitter.offsetWidth;

    // Calculate percentage widths
    let leftPanePercentage = (pointerRelativeXpos / containerWidth) * 100;
    let rightPanePercentage = 100 - leftPanePercentage - (splitterWidth / containerWidth) * 100;

    // Set minimum widths to prevent collapse
    const minPercentage = (50 / containerWidth) * 100; // Convert 50px to percentage

    if (leftPanePercentage < minPercentage) {
      leftPanePercentage = minPercentage;
      rightPanePercentage = 100 - minPercentage - (splitterWidth / containerWidth) * 100;
    } else if (rightPanePercentage < minPercentage) {
      rightPanePercentage = minPercentage;
      leftPanePercentage = 100 - minPercentage - (splitterWidth / containerWidth) * 100;
    }

    // Apply new widths
    this.leftPane.style.flexBasis = `${leftPanePercentage}%`;
    this.rightPane.style.flexBasis = `${rightPanePercentage}%`;

    this.saveState(leftPanePercentage);
  }
}
