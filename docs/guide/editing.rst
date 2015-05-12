.. _editing:

Editing Documents
=================

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

Document Content
----------------

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

Editing Content
---------------

TODO:

- HOWTO: edit a section, such as fixing a typo or applying a consolidation
- HOWTO: add a new chapter, part or section
- HOWTO: add a 
