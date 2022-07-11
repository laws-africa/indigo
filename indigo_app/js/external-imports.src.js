/**
 * These are imports from external npm libraries that must be compiled using webpack and then injected
 * into the window global for Indigo to use them.
 *
 * This provides a bridge between Indigo's lack of any support for 'import', and ES6-style imports.
 */
import * as indigoAkn from '@lawsafrica/indigo-akn';
import { fromRange as textPositionFromRange } from 'dom-anchor-text-position';
window.indigoAkn = indigoAkn;
window.textPositionFromRange = textPositionFromRange;
