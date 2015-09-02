.. _editing:

Editing Documents
=================

There are two major aspects of a document that you can edit: the **metadata** and the **content**. In this section we cover editing of both of these.

Metadata
--------

The metadata is important for describing the document and making it available through
the API.

.. image:: metadata.png

Basic Details
.............

**Short title** is the generally used title of the document. Most pieces of legislation declare what the short title will be.

**Country** the country that this legislation is applicable to.

**Locality** (optional) the area within the country that this legislation applies to. This is not applicable for national legislation and can be left blank.
If used, this should be a widely accepted code for the region. For example, in South Africa the list of municipality codes is `available on Wikipedia <http://en.wikipedia.org/wiki/List_of_municipalities_in_South_Africa>`_.

**Language** is the language of the document.

**Document subtype** (optional) is the subtype of the document. Choose **(none)** for general Acts.

**Year** is the year of the document, generally the year it was first introduced in Parliament.

**Number** is the number of the document within the year. Most Acts are assigned a sequential number within the year of introduction. If you don't have a number available (eg. for by-laws) use a reasonable short form of the document's name or, as a last resort, use ``nn`` for *not numbered*. Use ``cap123`` for Chapter 123 in a Cap-based numbering system.

**FRBR Work URI** is the URI used to identify this document and is calculated from the other metadata. It uniquely identifies this work. You cannot edit this value.

**Tags** is a free-form collection of tags for this document. Use tags to manage your documents during editing and even after publication. To add a new tag, click in the box, type a new tag and press enter or comma. You can add as many tabs as you like. To delete a tag, either backspace or click the **x** next to the tag's name.

**Stub document** indicates that the document doesn't have all its content yet. This is useful when other documents reference this one but no source is available
or the source has not been fully checked.

.. note::

    Administrators can add new countries, languages and document subtypes through the Admin interface.


Promulgation
............

**Publication date** (optional) is the date on which this document was officially published, in the format ``YYYY-MM-DD``.

**Publication name** (optional) is the name of the publication in which it was published, such as *National Gazette*.

**Publication number** (optional) is the number of the publication in which it was published, such as a gazette number.

**Assent date** (optional) is the date on which the President or other authority assented to the document, in the format ``YYYY-MM-DD``.

**Commencement date** (optional) is the date on which the bulk of the document comes into force, in the format ``YYYY-MM-DD``. If parts of the document come into force on different dates, place an editorial comment inline in the document indicating this.

Draft and Publishing
....................

**Draft** controls whether the document is available publically. While you are editing the document, this should be **checked**. Outside users cannot see draft documents. Once a document is ready to be used by outside users, uncheck this box to indicate it is published.

.. note:: You cannot delete a published document. Mark it as a draft, first.

Amendments
----------

The Amendments section records amendments that have been applied to reach **this version of the document**. If you are not editing the latest
version of the document this must only include those amendments that have been applied to reach this point.

To record an amendment, you need the following information about the **amending document** (the document that caused the amendments to happen):

- the title
- date of publication (date at which the amendments took place)
- the FRBR URI of the document

If the amending document is already in the library, you can choose it from the list and have all these details filled in automatically.

To create a newly amended version of a document, edit the version just before the new amendments need to be applied and click **Clone Document**
to create a copy, and then edit that copy.

Editing after Importing
-----------------------

If you're capturing a new document we recommend first capturing it using a standard word processor like Microsoft Word. Once you have the bulk of the document, import it into Indigo.

When Indigo first imports a document it extracts the textual content from the document runs it through a grammar. The grammar attempts to extract the structure of the document. It identifies structure based on the content of the document and by looking for keywords such as *chapter* and *part*. It breaks the document down into these structural elements:

- Preamble
- Parts and chapters (if any)
- Sections, subsections and numbered lists
- Schedules

.. note::

    Indigo ignores presentation details such as font size, bold and italicised text, and indentation because those elements are used inconsistently by different authors. Indigo will apply new presentation rules based on the structure of the document.

Once you have imported a document you will need to proof it to ensure that the various components have been correctly captured. The grammar doesn't always get everything right. In particular, look for these errors after importing:

- Check that parts and chapters have been identified correctly.
- Check that numbered sections have been identified correctly.
- Check that numbered lists aren't broken in the wrong places.
- Check that schedules have been matched correctly.


Basic Editing
-------------

The easiest way to make an edit is to use the Table of Contents on the left part of the document page to find the section in which to make the change.

1. Click on the heading of the part, chapter or section you wish to edit. Choose the smallest element that contains what you wish to change.

    .. image:: edit-choose-section.png

2. Click the **Edit** button in the top right corner of the document.

    .. image:: edit-button.png

3. Indigo will show the simple editor. Notice that the content of the editor is the textual content of the section you're editing, without any formatting and with very simple layout.
4. Make the changes you require.
5. Click the **green tick** at the top-right corner where you clicked the **Edit** button.

    .. image:: edit-inline.png

6. Indigo will process your change and replace the editor with the new content.

   - If you've made an edit Indigo cannot understand, clicking the **green tick** will show an error. Correct your edit and try again.
   - To abandon your changes, click the **X** icon near the green tick.

8. Click the blue **Save** button to save your changes to the server.

    .. image:: edit-save.png


.. note::

    Bear these tips in mind when editing:

    - Indigo can take a long time to process large sections. Choose the smallest containing element when editing.
    - Use the existing content as a guide for how to format new content.


The Simple Editor
-----------------

The editing mode shown above is Indigo's Simple Editor. It hides the XML completely and is suitable for most simple types of legislation. It requires following a few simple conventions and can generate the appropriate XML for you. It is simpler than working with the Akoma Ntoso XML directly.

Here is an example of the simple formatting required by the Simple Editor::

    Chapter 8
    Environmental management co-operation agreements

    35. Conclusion of agreements

    (1) The Minister and every MEC and municipality, may enter into environmental management co-operation agreements with any person or community for the purpose of promoting compliance with the principles laid down in this Act.

    (Section 35(1) inserted by section 7 of Act 46 of 2003)

    (2) Environmental management co-operation agreements must- 

    (a) only be entered into with the agreement of-

    (i) every organ of state which has jurisdiction over any activity to which such environmental management co-operation agreement relates;

    (ii) the Minister and the MEC concerned;

    (b) only be entered into after compliance with such procedures for public participation as may be prescribed by the Minister; and

    (c) comply with such regulations as may be prescribed under section 45.

Indigo understands how to convert the above into the XML that represents a chapter, section 35, subsections etc.

You can think of this as focusing on the **content** of the document and using
very simple **presentation** rules guided by a rough understanding of the
**structure**. Compare this with an editor like Word which focuses heavily on the **presentation**
of the content.

Notice that under subsection 1(a) above there is a sublist with items (i) and (ii). We don't bother
trying to indicate that it is a sublist, Indigo will work that out based on the numbering.

Simple Editor Guidelines
------------------------

When using the Simple Editor, follow these guidelines:

- Start the preface with::

      PREFACE

- Start the preamble with::

      PREAMBLE

- Start a chapter numbered ``N`` with::
      
      Chapter N
      Title

- Start a part numbered ``N`` with::

      Part N
      Title

- Start a section numbered ``N`` with::

      N. Title

- Numbered subsections must have a number in parentheses at the start of the line::

      (1) The content of section 1.

      (2) The content of section 2.

- Subsections or statements without numbers can be written as-is::

      A statement without a number.

- Numbered sublists must have a number in parentheses at the start of the line::

      (a) sublist item a

      (b) sublist item b

- Start a numbered Schedule with::

      Schedule N
      Title

  Both the number ``N`` and ``Title`` are optional. If a schedule doesn't have these, just use the
  word ``Schedule``.


Editing Tables
--------------

Often a piece of legislation will include tables, for example in Schedules. These can be tricky to edit
using the Simple Editor. Indigo uses the same text format for tables that `Wikipedia <http://wikipedia.org/>`_ uses.

.. seealso::

    Be sure to read `Wikipedia's tutorial for writing tables <http://en.wikipedia.org/wiki/Help:Table/Manual_tables>`_.

    **Don't use** ``class="wikitable"`` even though they recommend it.

This code::

    {|
    |-
    ! header 1
    ! header 2
    ! header 3
    |-
    | row 1, cell 1
    | row 1, cell 2
    | row 1, cell 3
    |-
    | row 2, cell 1
    | row 2, cell 2
    | row 2, cell 3
    |}

produces a table that looks like this:

============= ============= =============
Header 1      Header 2      Header 3
============= ============= =============
row 1, cell 1 row 1, cell 2 row 1, cell 3
row 1, cell 1 row 1, cell 2 row 1, cell 3
============= ============= =============

Notice how we don't explicitly make the header row bold. We simply indicate in the **structure** that those cells
are headers by using ``!`` at the start of the cell's line instead of the normal ``|``. Indigo will format the cell appropriately.


Viewing the XML
---------------

It can be useful to see what the Akoma Ntoso for a piece of the document looks like. Click the **Show Code** button to do this:

.. image:: show-code.png


Adding new Chapters, Parts and Sections
---------------------------------------

You can easily add a new chapter, part or section to a document. To do so:

1. edit the chapter, part or section just before where the new one needs to go
2. at the bottom, add the new chapter, part or section heading and content
3. click the green Update button

Advanced Editing
----------------

Indigo also has an advanced editing mode that uses the `LIME editor <http://lime.cirsfid.unibo.it/>`_ from the creators of Akoma Ntoso. This editor exposes some of the details of the Akoma Ntoso markup structure. It allows you to use the full expressiveness of Akoma Ntoso, but is more complicated to use than the Simple Editor and requires that you understand the Akoma Ntoso format.

To edit a document or section in the Advanced Editor, click the **Advanced Editor** button in the top-right corner near the Simple Editor button.

.. image:: edit-lime.png

Editing in the Advanced Editor is like painting with a paintbrush.

1. Write (or cut-and-paste) the content you wish to add
2. Highlight the text you want to mark
3. Click the markup element in the Document Markup pane to mark the highlighted text.

You can preview your changes by changing back to the Simple Editor by clicking the **Simple Editor** button to the left of the **Advanced Editor** button.
