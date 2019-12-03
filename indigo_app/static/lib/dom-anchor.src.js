var datp = require('dom-anchor-text-position');
var datq = require('dom-anchor-text-quote');
var seek = require('dom-seek');

window.textPositionFromRange = datp.fromRange;
window.textPositionToRange = datp.toRange;
window.textQuoteFromRange = datq.fromRange;
window.textQuoteFromTextPosition = datq.fromTextPosition;
window.textQuoteToRange = datq.toRange;
window.textQuoteToTextPosition = datq.toTextPosition;
window.domSeek = seek;
