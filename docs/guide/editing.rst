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

**Document subtype** (optional) is the subtype of the document. This must be left blank for general Acts. Otherwise, use the following abbreviations:

- For By-laws use **by-law**
- For Statutory Instruments use **si**
- For Government Notices use **gn**
- For Proclamations use **p**

**Year** is the year of the document, generally the year it was first introduced in Parliament.

**Number** is the number of the document within the year. Most Acts are assigned a sequential number within the year of introduction. If you don't have a number available (eg. for by-laws) use a reasonable short form of the document's name or, as a last resort, use ``nn`` for *not numbered*.

**FRBR Work URI** is the URI used to identify this document and is calculated from the other metadata. It uniquely identifies this work. You cannot edit this value.

**Tags** is a free-form collection of tags for this document. Use tags to manage your documents during editing and even after publication. To add a new tag, click in the box, type a new tag and press enter or comma. You can add as many tabs as you like. To delete a tag, either backspace or click the **x** next to the tag's name.

**Stub document** indicates that the document doesn't have all its content yet. This is useful when other documents reference this one but no source is available
or the source has not been fully checked.


Important Dates
...............

**Publication date** (optional) is the date on which this document was officially published, in the format ``YYYY-MM-DD``.

**Publication name** (optional) is the name of the publication in which it was published, such as *National Gazette*.

**Publication number** (optional) is the number of the publication in which it was published, such as a gazette number.

**Assent date** (optional) is the date on which the President or other authority assented to the document, in the format ``YYYY-MM-DD``.

**Commencement date** (optional) is the date on which the bulk of the document comes into force, in the format ``YYYY-MM-DD``. If parts of the document come into force on different dates, place an editorial comment inline in the document indicating this.

Draft and Publishing
....................

**Draft** controls whether the document is available publically. While you are editing the document, this should be **checked**. Outside users cannot see draft documents. Once a document is ready to be used by outside users, uncheck this box to indicate it is published.

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

3. Indigo will show the in-place editor. Notice that the content of the editor is the textual content of the section you're editing, without any formatting and with very simple layout.
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

Adding new Chapters, Parts and Sections
---------------------------------------

You cannot add a new section, part or chapter when editing an existing section, part or chapter. To add a new one, you must edit the element which *contains* an existing section, part or chapter.

For example, suppose you had the following layout and you need to add a new section "10. Staffing".

- Part 2 Institutional Matters

  - 7. First meeting
  - 8. Election of chairperson
  - 9. Meetings

You *cannot* add the new section by editing section "9. Meetings" and adding "10. Staffing at the end", Indigo will give you an error.

You must edit the element which *contains* an existing section near the one you wish to add. In this case, you would edit "Part 2 Institutional Matters" and add the new section at the end of section 9.

Similarly, if you needed to add "Part 3 Powers and duties" after Part 2, you would need to edit the entire document and add the new part after Part 2.

Editing Tables
--------------

TODO

Viewing the XML
---------------

It can be useful to see what the Akoma Ntoso for a piece of the document looks like. Click the **Show Code** button to do this:

.. image:: show-code.png
