var datp = require('dom-anchor-text-position');
var datq = require('dom-anchor-text-quote');
var he = require('he');

// these are used for attaching/detaching annotations, see:
// indigo/views/annotations.js
// indigo/dom.js
window.textPositionFromRange = datp.fromRange;
window.textQuoteFromTextPosition = datq.fromTextPosition;
window.textQuoteToTextPosition = datq.toTextPosition;

// for parsing HTML to XML, see dom.js
window.he = he;
