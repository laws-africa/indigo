Explicit text formatting
========================

Tables, cells and paragraphs support these authored class tokens. More specific
settings override inherited settings; unrelated classes are preserved.

* ``akn--text-normal``: the PDF document's normal size; 100% in Law Widgets.
* ``akn--text-small``: 8 pt in PDF; 80% in Law Widgets.
* ``akn--text-xsmall``: 7 pt in PDF; 70% in Law Widgets.
* ``akn--text-xxsmall``: 6 pt in PDF; 60% in Law Widgets.
* ``akn--text-left``, ``akn--text-center``, ``akn--text-right`` and
  ``akn--text-justify``: explicit text alignment.
* ``akn--no-padding`` on a table or cell: remove cell padding, retaining borders.

Size tiers are anchored to document size, so repeating a class on a descendant
does not compound a reduction. HTML applications can set
``--akn-base-font-size`` on the document container to match their document size.
These utilities do not change generic Indigo's unclassified-table defaults.
Annual Supplement defaults and legacy wide-table compatibility are configured
by the Kenya deployment.

The table editor groups table-wide size, alignment and padding controls in a
Bootstrap Table Formatting dropdown, including the whole-table Remove cell
borders checkbox. Border settings do not require a cell selection. A text-size
dropdown beside Bold, Italic and Underline applies to the selected cells; cell
alignment buttons remain in the toolbar. The table dropdown stays open while
changing its controls. Default removes only the chosen class group. Left writes an explicit class. Mixed cell sizes are shown
as Mixed; cell controls are disabled without a selection. Classified paragraphs
inside cells are preserved but have no general paragraph toolbar in this change.
The editor retains any deprecated table ``fontsize`` attribute directly from
the original XML when saving. HTML rendering, CKEditor filtering and HTML-to-AKN
conversion do not support that attribute; new controls do not create it.
Select Normal to override legacy wide-table sizing explicitly.

Browser regression checks
-------------------------

Install development dependencies, then run::

    CHROME_BIN=/path/to/chrome npm run test:table-editor

The test serves local fixtures and runs actual CKEditor filtering and
HTML-to-AKN conversion. It exercises unchanged save, formatting changes,
cancel, mixed selections, disabled controls, and explicit Left versus Default.
Set ``INDIGO_AKN_SOURCE=/path/to/indigo-akn`` to test an unreleased checkout;
otherwise the installed dependency is used. The updated converter is required.

Dependency release coordination
-------------------------------

The compiled assets in this review use Law Widgets commit
``a4d68bffc9c3c317996b9e991d079902921cfc65`` and indigo-akn commit
``8c352b22b03bf2d940965d2aff93f4d1edd82128``. Their source branches are
``as-table-classes`` in the corresponding repositories.

Package publication is a separate step. The npm manifests still reference the
existing published versions; update those dependencies and the lock file after
publishing the reviewed packages, before rebuilding assets for a release.
