/**
 * These are imports from local libraries that must be compiled using browserify and then injected
 * into the window global for Indigo to use them.
 *
 * This provides a bridge between Indigo's lack of any support for require() or 'import', and require-js and
 * ES6-style imports.
 */

import * as enrichments from './enrichments/popups';
window.enrichments = enrichments;
