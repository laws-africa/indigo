/**
 * Helper class to determine the vertical layout of a collection of gutter content elements, such that they are aligned
 * vertically with their anchor elements, but don't overlap each other.
 *
 * Item objects must have:
 *
 * * a `anchorElement` attribute, which is the reference element to position the item in line with
 * * a `top` setter, which will be called with the new top pixel value
 */
export class GutterLayout {
  /**
   * @param root root element for determining heights against. This MUST have a position style attribute,
   *             such as position: relative;
   */
  constructor (root) {
    this.root = root;
    // vertical buffer between elements
    this.buffer = 10;
    this.tops = null;
  }

  layout (items, activeItem) {
    // pre-calculate tops
    this.updateTops(items);

    // sort items by ascending anchorElement top
    items = [...items].sort((a, b) => this.tops.get(a.anchorElement) - this.tops.get(b.anchorElement));

    if (activeItem) {
      const ix = items.indexOf(activeItem);
      if (ix > -1) {
        // layout the primary item first
        const top = this.tops.get(activeItem.anchorElement);
        activeItem.top = top;
        // layout the ones going upwards from here
        this.layoutUpwards(items, ix - 1, top - this.buffer);
        // layout the ones going downwards from here
        this.layoutDownwards(items, ix + 1, top + activeItem.contentElement.clientHeight + this.buffer);
        return;
      }
    }

    // nothing is primary, go top downwards
    this.layoutDownwards(items, 0, 0);
  }

  layoutUpwards (items, start, watermark) {
    // layout the items from index start, going bottom to top
    for (let i = start; i >= 0; i--) {
      const item = items[i];
      let top = this.tops.get(item.anchorElement);
      if (top + item.contentElement.clientHeight >= watermark) {
        top = watermark - item.contentElement.clientHeight;
      }
      item.top = top;
      watermark = top - this.buffer;
    }
  }

  layoutDownwards (items, start, watermark) {
    // layout the items from index start, going top to bottom
    for (let i = start; i < items.length; i++) {
      const item = items[i];
      const top = Math.max(watermark, this.tops.get(item.anchorElement));
      item.top = top;
      watermark = top + item.contentElement.clientHeight + this.buffer;
    }
  }

  updateTops (items) {
    this.tops = new WeakMap();

    for (const item of items) {
      const anchor = item.anchorElement;
      if (!this.tops.has(anchor)) {
        this.tops.set(anchor, this.calculateTop(anchor));
      }
    }
  }

  /**
   * Find the top of an element, relative to this.root.
   * @param element
   * @returns {number}
   */
  calculateTop (element) {
    let top = 0;

    while (element && element !== this.root) {
      top += element.offsetTop;
      element = element.offsetParent;
    }

    return top;
  }
}
