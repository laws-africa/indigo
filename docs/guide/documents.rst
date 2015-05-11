Editing Documents
=================

Library
-------

The library lists all the documents in the system. You can filter them by country and by tag and search for them by title, year and number.


.. image:: library.png


Searching
.........

Search for a document by typing in the search box. This will limit the documents to only those that match your search. Searches ignore case and
match against title, year and number. Clear the search by clicking the **x** button.


Filtering by Country
....................

To show only documents for a particular country click the name of the country in the list on the right.


Filtering by Tag
................

Tags are a powerful way to group and manage documents however you need to. You can add as many tags as you like to a document.

Change a document's tags by clicking on the document name and changing them in the **Basic details** section of the Properties
page.

You can filter the documents to show only those with one or more tags. To do so, click the tag in the list of tags on the right.
The number next to the tag is the number of documents that have that tag. Tags you are filtering by are highlighted in blue.

If you choose to filter by multiple tags, only documents with all of the chosen tags will be shown.


Importing a new document
------------------------

You can create a new document by importing an existing document such as a PDF or a Word file. Indigo supports
a wide range of document types through the use of `Apache Tika <https://tika.apache.org/>`_. However, simple
documents such as Word (.doc) and RTF produce the best results.

.. note::

    Follow these tips for getting the best results when importing documents:

    - Prefer RTF or Word (.doc) documents, use PDFs only as a last resort
    - Remove the Table of Contents
    - Convert images to text

To import a document:

1. Click the arrow next to the **Library** button and choose **Import a document**.
2. Drag and drop the file to import into the box, or click the button to choose a file to upload.
3. Wait for the document to be imported. This make take up to 10 minutes, especially for large documents.

Once the document has been imported Indigo will take you to the details for that document.

You will also need to proof the document to ensure Indigo imported it correctly. See the
section on `Editing`_ for more details.

Indigo will do its best to extract text information from the imported document.
You will still need to fill in all the metadata such as the document title,
year of publication, etc.

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

**Document subtype** (optional) is the subtype of the document, beyond just being an Act. This can generally be left blank. In South Africa, this must be ``by-law`` for by-laws.

**Year** is the year of the document, generally the first year it was introduced in Parliament.

**Number** is the number of the document. Most Acts are assigned a number. If you don't have a number available (eg. for by-laws), use a reasonable short form of the document's name.


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


Editing
-------


Deleting a document
-------------------

You can delete a document by going to the document Properties page and scrolling down to the **Danger Zone** section
and clicking the **Delete this document** button.

.. note::

    If you delete a document by accident an administrator can undelete it for you.

    Administrators: visit ``/admin/indigo_api/document/`` and click on the document to recover, scroll down
    to find the **Deleted** checkbox, uncheck it and click **Save**.
