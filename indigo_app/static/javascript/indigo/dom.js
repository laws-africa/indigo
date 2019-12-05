$(function() {
  if (!Indigo.dom) Indigo.dom = {};

  /**
   * Removes foreign elements from the tree at root, executes callback,
   * and then replaces the foreign elements.
   *
   * This is useful for annotations because we inject foreign (ie. non-Akoma Ntoso)
   * elements into the rendered AKN document, such as table editor buttons, annotations
   * and issue indicators.
   *
   * @returns the result of callback()
   */
  Indigo.dom.withoutForeignElements = function(root, callback, selector) {
    var result,
      removed = [];

    selector = selector || '.ig';

    // remove the foreign elements
    root.querySelectorAll(selector).forEach(function(elem) {
      var info = {e: elem};

      // store where the element was in the tree
      if (elem.nextSibling) info.before = elem.nextSibling;
      // no next sibling, it's the last child
      else info.parent = elem.parentElement;

      elem.parentElement.removeChild(elem);
      removed.push(info);
    });

    result = callback();

    // put the elements back
    removed.forEach(function(info) {
      if (info.before) info.before.parentElement.insertBefore(info.e, info.before);
      else info.parent.appendChild(info.e);
    });

    return result;
  }

  /**
   * Given a browser Range object, transform it into a target description
   * suitable for use with annotations.
   */
  Indigo.dom.rangeToTarget = function(range) {
    var anchor = range.commonAncestorContainer,
      target = {selectors: []},
      selector;

    // TODO: handle no id element (ie. body, preamble, etc.)
    anchor = $(anchor).closest('[id]')[0];
    // TODO: data-id?
    target.anchor_id = anchor.id;

    Indigo.dom.withoutForeignElements(anchor, function() {
      // position selector
      selector = textPositionFromRange(anchor, range);
      selector.type = "TextPositionSelector";
      target.selectors.push(selector);

      // quote selector, based on the position
      selector = textQuoteFromTextPosition(anchor, selector);
      selector.type = "TextQuoteSelector";
      target.selectors.push(selector);
    });

    return target;
  };

  /**
   * Convert a Target object (anchor_id, selectors) to Range object.
   */
  Indigo.dom.targetToRange = function(target) {
    var node, range;

    node = document.getElementById(target.anchor_id);
    // TODO: try harder
    if (!node) return;

    if (!target.selectors) {
      // no selectors, old-style annotation for an entire element
      range = document.createRange();
      range.selectNodeContents(node);
      return range;
    }

    // TODO: if we don't have an anchor, then try walking up the anchor chain until we can find a target.
    return Indigo.dom.withoutForeignElements(node, function() {
      return Indigo.dom.selectorsToRange(node, target.selectors);
    });
  };

  /**
   * Given a root and a list of selectors, convert it into a browser Range object.
   */
  Indigo.dom.selectorsToRange = function(anchor, selectors) {
    var posnSelector = _.findWhere(selectors, {type: "TextPositionSelector"}),
      quoteSelector = _.findWhere(selectors, {type: "TextQuoteSelector"}),
      range;

    if (posnSelector) {
      range = textPositionToRange(anchor, posnSelector);

      // compare text with the exact from the quote selector
      if (quoteSelector && range.toString() === quoteSelector.exact) {
        return range;
      }
    }

    // fall back to the quote selector
    if (quoteSelector) {
      return textQuoteToRange(anchor, quoteSelector);
    }
  };

  /* Mark all the text nodes in a range with a given tag (eg. 'mark')
   */
  Indigo.dom.markRange = function(range, tagName, callback) {
    var iterator, node, posn,
      nodes = [],
      start, end,
      ignore = {'TABLE': 1, 'THEAD': 1, 'TBODY': 1, 'TR': 1};

    function split(node, offset) {
      // split the text node so that the offsets fall on text node boundaries
      if (offset !== 0) {
        return node.splitText(offset);
      } else {
        return node;
      }
    }

    node = range.commonAncestorContainer;
    if (node.nodeType != Node.ELEMENT_NODE) node = node.parentElement;

    // remove foreign elements while working with the range
    Indigo.dom.withoutForeignElements(node, function() {
      if (range.startContainer.nodeType === Node.TEXT_NODE) {
        // split the start and end text nodes so that the offsets fall on text node boundaries
        start = split(range.startContainer, range.startOffset);
      } else {
        // first text node
        start = document.createNodeIterator(range.startContainer, NodeFilter.SHOW_TEXT).nextNode();
        if (!start) return;
      }

      if (range.endContainer.nodeType === Node.TEXT_NODE) {
        end = split(range.endContainer, range.endOffset);
      } else {
        end = range.endContainer;
      }

      // gather all the text nodes between start and end
      iterator = document.createNodeIterator(
        range.commonAncestorContainer, NodeFilter.SHOW_TEXT,
        function (n) {
          // ignore text nodes in weird positions in tables
          if (ignore[n.parentElement.tagName]) return NodeFilter.FILTER_SKIP;
          return NodeFilter.FILTER_ACCEPT;
        });

      // advance until we're at the start node
      node = iterator.nextNode();
      while (node && node !== start) node = iterator.nextNode();

      // gather text nodes
      while (node) {
        posn = node.compareDocumentPosition(end);
        // stop if node isn't inside end, and doesn't come before end
        if ((posn & Node.DOCUMENT_POSITION_CONTAINS) === 0 &&
          (posn & Node.DOCUMENT_POSITION_FOLLOWING) === 0) break;

        nodes.push(node);
        node = iterator.nextNode();
      }
    });

    // mark the gathered nodes
    nodes.forEach(function(node) {
      var mark = document.createElement(tagName);
      node.parentElement.insertBefore(mark, node);
      mark.appendChild(node);
      if (callback) callback(mark);
    });
  };
});
