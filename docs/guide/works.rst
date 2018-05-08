Works and the Library
=====================

A work is an Act, a by-law, a regulation, and so on. In Indigo, a work doesn't
have any content -- it's just a description of the basic details of the act (or
by-law, etc.). A work can be associated with many documents, each of which is an
*expression* of the work.

An Indigo work is uniquely identified by its FRBR URI. Documents are linked to a work through
a common FRBR URI.

Documents inherit a number of fields from a work, such as the FRBR URI, publication date, repeal status, etc.
These details are managed at the work level, not at the document level.

You must create a work before you can import a new document.

Library
-------

The library lists all the works and documents in the system. You can filter them by country and by tag and search for them by title, year and number.


.. image:: library.png


Searching
.........

Search for a document by typing in the search box. This will limit the documents to only those that match your search. Searches ignore case and
match against title, year and number. Clear the search by clicking the **x** button.


Filtering by Country
....................

To show only documents for a particular country, choose the name of the country from the list.


Filtering by Tag
................

Tags are a powerful way to group and manage documents however you need to. You can add as many tags as you like to a document.

Change a document's tags by clicking on the document name and changing them in the **Basic details** section of the Properties
page.

You can filter the documents to show only those with one or more tags. To do so, click the tag in the list of tags on the right.
The number next to the tag is the number of documents that have that tag. Tags you are filtering by are highlighted in blue.

If you choose to filter by multiple tags, only documents with all of the chosen tags will be shown.

Editing Works
-------------

To edit a work, click through to the work from the library or a linked document.

To create a new work, use the **New Work** option in the library menu.

Work Details
------------

**Short title** is the generally used title of the work. Most pieces of legislation declare what the short title will be.

**Country** the country that this legislation is applicable to.

**Locality** (optional) the area within the country that this legislation applies to. This is not applicable for national legislation and can be left blank.
If used, this should be a widely accepted code for the region. For example, in South Africa the list of municipality codes is `available on Wikipedia <http://en.wikipedia.org/wiki/List_of_municipalities_in_South_Africa>`_.

**Document subtype** (optional) is the subtype of the work. Choose **(none)** for general Acts.

**Year** is the year of the work, generally the year it was first introduced in Parliament.

**Number** is the number of the work within the year. Most Acts are assigned a sequential number within the year of introduction. If you don't have a number available (eg. for by-laws) use a reasonable short form of the work's name or, as a last resort, use ``nn`` for *not numbered*. Use ``cap123`` for Chapter 123 in a Cap-based numbering system.

**FRBR Work URI** is the URI used to identify this work and is calculated from the other metadata. It uniquely identifies this work. You cannot edit this value.

.. note::

    Administrators can add new countries and subtypes through the Admin interface. Click on your name in the top-right corner and choose **Site Settings**.

Promulgation
............

**Publication date** (optional) is the date on which this work was officially published, in the format ``YYYY-MM-DD``.

**Publication name** (optional) is the name of the publication in which it was published, such as *National Gazette*.

.. note::

    Administrators can set the publication names which are available in the drop-down list. Click on your name in the top-right corner and choose **Site Settings**, then edit a country in the Indigo Editor section.

**Publication number** (optional) is the number of the publication in which it was published, such as a gazette number.

**Assent date** (optional) is the date on which the President or other authority assented to the work, in the format ``YYYY-MM-DD``.

**Commencement date** (optional) is the date on which the bulk of the work comes into force, in the format ``YYYY-MM-DD``. If parts of the work come into force on different dates, place an editorial comment inline in the document indicating this.

Repeal
......

**Repealing work** The work which repealed this work, if any.

**Repeal date** (optional) is the date on which the work was repealed, in the format ``YYYY-MM-DD``.
