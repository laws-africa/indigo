/*jshint esversion: 6 */

$(function() {
  if (!Indigo.dom) Indigo.dom = {};

  // Selector for elements that are foreign to AKN documents, such as table editor buttons
  // and annotations.
  Indigo.dom.foreignElementsSelector = '.ig';

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

    selector = selector || Indigo.dom.foreignElementsSelector;

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

    try {
      result = callback();
    } finally {
      // put the elements back, even if result throws an error
      removed.reverse();
      removed.forEach(function (info) {
        if (info.before) info.before.parentElement.insertBefore(info.e, info.before);
        else info.parent.appendChild(info.e);
      });
    }

    return result;
  };

  /**
   * Given a browser Range object, transform it into a target description
   * suitable for use with annotations. Will not go above root, if given.
   */
  Indigo.dom.rangeToTarget = function(range, root) {
    var anchor = range.commonAncestorContainer,
        target = {selectors: []},
        selector;

    anchor = $(anchor).closest('[id]')[0];
    if (root && anchor !== root &&
      (anchor.compareDocumentPosition(root) & Node.DOCUMENT_POSITION_CONTAINS) === 0) return;
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
   *
   * This does its best to try to find a match, walking up the anchor hierarchy if possible.
   */
  Indigo.dom.targetToRange = function(target) {
    var anchor, range,
        anchor_id = target.anchor_id,
        ix = anchor_id.lastIndexOf('.');

    anchor = document.getElementById(anchor_id);

    if (!target.selectors) {
      // no selectors, old-style annotation for an entire element
      if (anchor) {
        range = document.createRange();
        range.selectNodeContents(anchor);
      }
      return range;
    }

    // do our best to find the anchor node, going upwards up the id chain if
    // the id has dotted components
    while (!anchor && ix > -1) {
      anchor_id = anchor_id.substring(0, ix);
      ix = anchor_id.lastIndexOf('.');
      anchor = document.getElementById(anchor_id);
    }

    if (!anchor) return;

    // remove foreign elements, then use the selectors to find the text
    // build up a Range object.
    return Indigo.dom.withoutForeignElements(anchor, function() {
      return Indigo.dom.selectorsToRange(anchor, target.selectors);
    });
  };

  /**
   * Given a root and a list of selectors, create browser Range object.
   *
   * Only TextPositionSelector and TextQuoteSelector types from https://www.w3.org/TR/annotation-model/
   * are used.
   */
  Indigo.dom.selectorsToRange = function(anchor, selectors) {
    var posnSelector = _.findWhere(selectors, {type: "TextPositionSelector"}),
      quoteSelector = _.findWhere(selectors, {type: "TextQuoteSelector"}),
      range;

    if (posnSelector) {
      try {
        range = Indigo.dom.textPositionToRange(anchor, posnSelector);
        // compare text with the exact from the quote selector
        if (quoteSelector && range.toString() === quoteSelector.exact) {
          return range;
        }
      } catch (err) {
        // couldn't match to the position, try the quote selector instead
      }
    }

    // fall back to the quote selector
    if (quoteSelector) {
      return Indigo.dom.textQuoteToRange(anchor, quoteSelector);
    }
  };

  /**
   * Mark all the text nodes in a range with a given tag (eg. 'mark'),
   * calling the callback for each new marked element.
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
      var mark = document.createElement(tagName || 'mark');
      node.parentElement.insertBefore(mark, node);
      mark.appendChild(node);
      if (callback) callback(mark);
    });
  };

  /**
   * toRange from https://github.com/hypothesis/dom-anchor-text-position/blob/handle-end-of-root-selection/src/index.js
   */
  Indigo.dom.textPositionToRange = function(root, selector = {}) {
    if (root === undefined) {
      throw new Error('missing required parameter "root"');
    }

    let start = selector.start || 0;
    let end = selector.end || start;

    // Total character length of text nodes visited so far.
    let nodeTextOffset = 0;

    // Node and character offset where the start position of the selector occurs.
    let startContainer = null;
    let startOffset = 0;

    // Node and character offset where the end position of the selector occurs.
    let endContainer = null;
    let endOffset = 0;

    // Iterate over text nodes and find where the start and end positions occur.
    let iter = document.createNodeIterator(root, NodeFilter.SHOW_TEXT);
    while (iter.nextNode() && (startContainer === null || endContainer === null)) {
      let nodeTextLength = iter.referenceNode.nodeValue.length;

      if (startContainer === null &&
          start >= nodeTextOffset && start <= nodeTextOffset + nodeTextLength) {
        startContainer = iter.referenceNode;
        startOffset = start - nodeTextOffset;
      }
      if (endContainer === null &&
          end >= nodeTextOffset && end <= nodeTextOffset + nodeTextLength) {
        endContainer = iter.referenceNode;
        endOffset = end - nodeTextOffset;
      }

      nodeTextOffset += nodeTextLength;
    }

    if (!startContainer) {
      throw new Error('Start offset of position selector is out of range');
    }
    if (!endContainer) {
      throw new Error('End offset of position selector is out of range');
    }

    let range = root.ownerDocument.createRange();
    range.setStart(startContainer, startOffset);
    range.setEnd(endContainer, endOffset);

    return range;
  };

  /**
   * Given a root and a TextQuoteSelector, convert it to a Range object.
   *
   * Re-implements toRange from https://github.com/tilgovi/dom-anchor-text-quote
   * so that we can call our custom textPositionToRange()
   */
  Indigo.dom.textQuoteToRange = function(root, selector, options) {
    var posn = textQuoteToTextPosition(root, selector, options);
    if (posn) {
      // ensure posn.end doesn't exceed the length of the root text
      // see https://github.com/tilgovi/dom-anchor-text-quote/issues/16
      posn.end = Math.min(posn.end, root.textContent.length);
      return Indigo.dom.textPositionToRange(root, posn);
    }
  };

  /**
   * Serialize an HTML node to an XML string.
   *
   * This transforms from html -> string -> xhtml so that the XML is well formed.
   * It also ensures that entity references that are defined in HTML but not in XML
   * (eg. &nbsp;) are substituted for their unicode equivalents.
   */
  Indigo.dom.htmlNodeToXml = function(node) {
    // html -> string
    var xml = new XMLSerializer().serializeToString(node);

    // translate HTML entities that XML doesn't understand
    // 1. escape away valid XML entities
    //    https://en.wikipedia.org/wiki/List_of_XML_and_HTML_character_entity_references#Predefined_entities_in_XML
    xml = xml.replace(/&(quot|amp|apos|lt|gt);/g, '&la_$1;');
    // 2. decode named entities
    xml = he.decode(xml);
    // 3. put the valid XML entities back
    xml = xml.replace(/&la_(quot|amp|apos|lt|gt);/g, '&$1;');

    return xml;
  };

  /**
   * Transform an HTML node into an XML node.
   */
  Indigo.dom.htmlNodeToXmlNode = function(node) {
    return $.parseXML(Indigo.dom.htmlNodeToXml(node));
  };
});
