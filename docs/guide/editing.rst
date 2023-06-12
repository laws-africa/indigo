.. _editing:

Editing documents
=================

.. note::

    For a full guide to editing documents, see the `Laws.Africa markup guide <https://docs.laws.africa/markup-guide/>`_.

If you're capturing a new document we recommend first capturing it using a standard word processor like Microsoft Word, and then importing it into Indigo.

Indigo looks for structure in a document by looking for keywords such as *chapter* and *part*. It can identify different aspects of a document:

- Preface
- Preamble
- Parts and chapters
- Sections, subsections and paragraphs
- Schedules

.. note::

    Indigo ignores presentation details such as font size, bold and italicised text, and indentation because those elements are used inconsistently by different authors. Indigo will apply new presentation rules based on the structure of the document.


Making and saving changes
-------------------------

The easiest way to make an edit is to use the Table of Contents on the left part of the document page to find the section in which to make the change.

1. Click on the heading of the part, chapter or section you wish to edit. Choose the smallest element that contains what you wish to change.

    .. image:: edit-choose-section.png

2. Click the **Edit** button in the top right corner of the document.

    .. image:: edit-button.png

3. Indigo will show the simple editor. Notice that the content of the editor is the textual content of the section you're editing, without any formatting and with very simple layout.
4. Make the changes you require.
5. Click the **✔ Update** button.

    .. image:: edit-inline.png

6. Indigo will process your change and replace the editor with the new content.

   - If you've made an edit Indigo cannot understand, clicking the **✔ Update** button will show an error. Correct your edit and try again.
   - To abandon your changes, click the **× Cancel** button.

8. Click the **Save** button to save your changes to the server.

    .. image:: edit-save.png


.. note::

    Bear these tips in mind when editing:

    - Indigo can take a long time to process large sections. Choose the smallest containing element when editing.
    - Use the existing content as a guide for how to format new content.


Editing structure
-----------------

Indigo cares about the structure of a document, not font sizes or layout. This means you need to follow a few simple conventions and Indigo will do all the hard work for you.

Here is an example of the simple formatting used by Indigo::

    CHAPTER 8 - Environmental management co-operation agreements

      SECTION 35. - Conclusion of agreements

        SUBSECTION (1)

          The Minister and every MEC and municipality, may enter into environmental management co-operation agreements with any person or community for the purpose of promoting compliance with the principles laid down in this Act.

          {{*[subsection (1) inserted by section 7 of Act 46 of 2003]}}

        SUBSECTION (2)

          Environmental management co-operation agreements must- 

          PARAGRAPH (a)

            only be entered into with the agreement of-

            SUBPARAGRAPH (i)

              every organ of state which has jurisdiction over any activity to which such environmental management co-operation agreement relates;

            SUBPARAGRAPH (ii)

              the Minister and the MEC concerned;

          PARAGRAPH (b)

            only be entered into after compliance with such procedures for public participation as may be prescribed by the Minister; and

          PARAGRAPH (c)

            comply with such regulations as may be prescribed under section 45.

Indigo understands how to convert this into the XML that represents a chapter, section 35, etc, including a unique eId (element ID) for each element.

We explicitly name the hierarchical elements, as the conventions around what they look like can differ across jurisdictions.

We also explicitly indent elements and text that fall within an element, to indicate precisely where an element ends.

You can think of this as focusing on the **content** of the document and using
very simple **presentation** rules guided by an understanding of the
**structure**. Compare this with an editor like Word which focuses heavily on the **presentation**
of the content.

See the `Laws.Africa markup guide <https://docs.laws.africa/markup-guide/>`_ for more elements and mark-up examples.


Tables
------

Often a piece of legislation will include tables, for example in Schedules.

The easiest way to edit these is to click the **Edit table** button at the top of the table.

- Simply type your changes into the table and click **✔ Update** when you're done.

- Use the buttons in the toolbar to add and remove columns and rows, and to set cells as heading cells.

    .. image:: edit-table.gif

- To **merge** cells, use the mouse to select the cells and click **Merge cells**.

- To **split merged cells**, select the cells and click the **Merge cells** button again.

    .. image:: merge-cells.gif


Editing tables in the simple editor
...................................

You can also edit tables in the simple editor, and will have to when the table includes numbered elements or quotes.

This code::

  TABLE
    TR
      TH
        Header 1
      TH
        Header 2
      TH
        Header 3

    TR
      TC
        row 1, cell 1
      TC
        row 1, cell 2
      TC
        row 1, cell 3

    TR
      TC
        row 2, cell 1
      TC
        row 2, cell 2
      TC
        row 2, cell 3

produces a table that looks like this:

============= ============= =============
Header 1      Header 2      Header 3
============= ============= =============
row 1, cell 1 row 1, cell 2 row 1, cell 3
row 1, cell 1 row 1, cell 2 row 1, cell 3
============= ============= =============

Notice how we don't explicitly make the header row bold. We simply indicate in the **structure** that those cells
are headers by using ``TH`` instead of ``TC``. Indigo will format the cell appropriately.

See `Marking up tables <https://docs.laws.africa/markup-guide/marking-up-tables>`_ in the Laws.Africa markup guide for detailed instructions on working with tables.


Telling Indigo to ignore special items
--------------------------------------

Sometimes it's useful to be able to tell Indigo not to interpret a line or some inline markup specially. Do this by using a backslash ``\``.

This is particularly useful when a paragraph starts with a text that Indigo would normally interpret as a hierarchical element. For example::

   \CHAPTER 1 States that …
   This text \*\*should not\*\* be bold

Because ``\`` is used before the keyword and before the **\*\*bold\*\*** markup, Indigo knows to ignore them and treat is as normal text.


Links
-----

Add a link in the text of your document using this syntax::

    {{>http://example.com/page link text}}

That will create a link like this: `link text <http://example.com/page>`_


Images
------

You can embed an image in your document using this syntax::

    {{IMG media/image.png alternative text}}

That will create an image using the ``image.png`` file added to your document as an attachment.


Downloading PDF and standalone HTML
-----------------------------------

You can download PDF and standalone (self-contained) HTML versions of a document. These are useful for distribution and archiving. Click on **Settings** and **Download as**.
