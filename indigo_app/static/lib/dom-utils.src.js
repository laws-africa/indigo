var datp = require('dom-anchor-text-position');
var datq = require('dom-anchor-text-quote');
var domSeek = require('dom-seek');
var he = require('he');

window.textPositionFromRange = datp.fromRange;
window.textPositionToRange = datp.toRange;
window.textQuoteFromRange = datq.fromRange;
window.textQuoteFromTextPosition = datq.fromTextPosition;
window.textQuoteToRange = datq.toRange;
window.textQuoteToTextPosition = datq.toTextPosition;
window.domSeek = domSeek;
window.he = he;
