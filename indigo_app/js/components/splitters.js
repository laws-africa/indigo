export class VSplitter {
  constructor (splitter) {
    this.cursor = 'col-resize';
    this.splitter = splitter;
    this.container = splitter.parentElement;
    this.firstPane = splitter.previousElementSibling;
    this.secondPane = splitter.nextElementSibling;
    this.isDragging = false;

    this.splitter.addEventListener('mousedown', (e) => this.onMouseDown(e));
    this.mouseUp = this.onMouseUp.bind(this);
    this.mouseMove = this.onMouseMove.bind(this);

    if (this.splitter.id) {
      this.storageKey = `splitter:${this.splitter.id}`;
      this.loadState();
    } else {
      this.storageKey = null;
    }
  }

  loadState () {
    let percentage = window.localStorage.getItem(this.storageKey);
    if (percentage) {
      try {
        percentage = Math.max(10, Math.min(90, parseFloat(percentage)));
        this.setFirstPanePercentage(percentage);
      } catch {
        window.localStorage.removeItem(this.storageKey);
      }
    }
  }

  saveState (width) {
    if (this.storageKey) {
      window.localStorage.setItem(this.storageKey, width.toString());
    }
  }

  onMouseDown (e) {
    this.isDragging = true;
    document.body.classList.add('splitter-dragging');
    document.body.style.cursor = this.cursor;
    document.body.style.userSelect = 'none';
    document.addEventListener('mouseup', this.mouseUp);
    document.addEventListener('mousemove', this.mouseMove);
  }

  onMouseUp (e) {
    if (this.isDragging) {
      this.isDragging = false;
      document.body.classList.remove('splitter-dragging');
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

    this.setFirstPanePercentage((pointerRelativeXpos / containerWidth) * 100);
  }

  setFirstPanePercentage (leftPanePercentage) {
    const containerWidth = this.container.clientWidth;
    const splitterWidth = this.splitter.offsetWidth;

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
    this.firstPane.style.flexBasis = `${leftPanePercentage}%`;
    this.secondPane.style.flexBasis = `${rightPanePercentage}%`;

    this.saveState(leftPanePercentage);
  }
}

export class HSplitter extends VSplitter {
  constructor (splitter) {
    super(splitter);
    this.cursor = 'row-resize';
  }

  onMouseMove (e) {
    if (!this.isDragging) return;

    // Calculate new heights
    const containerOffsetTop = this.container.getBoundingClientRect().top;
    const pointerRelativeYpos = e.clientY - containerOffsetTop;
    const containerHeight = this.container.clientHeight;

    // Calculate percentage heights
    this.setFirstPanePercentage((pointerRelativeYpos / containerHeight) * 100);
  }

  setFirstPanePercentage (firstPanePercentage) {
    const containerHeight = this.container.clientHeight;
    const splitterHeight = this.splitter.offsetHeight;

    let bottomPanePercentage = 100 - firstPanePercentage - (splitterHeight / containerHeight) * 100;

    // Set minimum widths to prevent collapse
    const minPercentage = (50 / containerHeight) * 100; // Convert 50px to percentage

    if (firstPanePercentage < minPercentage) {
      firstPanePercentage = minPercentage;
      bottomPanePercentage = 100 - minPercentage - (splitterHeight / containerHeight) * 100;
    } else if (bottomPanePercentage < minPercentage) {
      bottomPanePercentage = minPercentage;
      firstPanePercentage = 100 - minPercentage - (splitterHeight / containerHeight) * 100;
    }

    // Apply new widths
    this.firstPane.style.flexBasis = `${firstPanePercentage}%`;
    this.secondPane.style.flexBasis = `${bottomPanePercentage}%`;

    this.saveState(firstPanePercentage);
  }
}
