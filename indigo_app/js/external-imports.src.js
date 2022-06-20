/**
 * These are imports from external npm libraries that must be compiled using browserify and then injected
 * into the window global for Indigo to use them.
 *
 * This provides a bridge between Indigo's lack of any support for require() or 'import', and require-js and
 * ES6-style imports.
 */
const datp = require('dom-anchor-text-position');
const datq = require('dom-anchor-text-quote');

// these are used for attaching/detaching annotations, see:
// indigo/views/annotations.js
// indigo/dom.js
window.textPositionFromRange = datp.fromRange;
window.textQuoteFromTextPosition = datq.fromTextPosition;
window.textQuoteToTextPosition = datq.toTextPosition;

// AKN utilities
import * as indigoAkn from '@lawsafrica/indigo-akn';
window.indigoAkn = indigoAkn;
