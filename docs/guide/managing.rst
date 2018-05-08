Managing Documents
==================

Importing a new document
------------------------

You can create a new document by importing an existing file, such as a PDF or a Word document. Indigo uses
`Apache Tika <https://tika.apache.org/>`_ to import from a wide range of document types, including:

- MS Word (.doc and .docx)
- Rich Text Format (.rtf)
- PDF
- Plain text (.txt)

Simple documents such as Word (.doc) and RTF produce the best results.

.. note::

    Follow these tips for getting the best results when importing documents:

    - Prefer RTF or Word (.doc and .docx) documents; use PDFs only as a last resort
    - Remove the Table of Contents at the start of the document
    - Convert images to text

To import a document:

1. Click the arrow next to the **Library** button and choose **Import a document**.
2. Drag and drop the file to import into the box, or click the button to choose a file to upload.
3. Wait for the document to be imported. This make take up to 10 minutes, especially for large documents.

Once you have imported a document you will need to proof it to ensure that the various components have been correctly captured. Indigo doesn't always get everything right. Look for these errors after importing:

- Check that parts and chapters have been identified correctly.
- Check that numbered sections have been identified correctly.
- Check that numbered lists aren't broken in the wrong places.
- Check that schedules have been matched correctly.

.. seealso::

    See the section on :ref:`editing` for more details.

Indigo will do its best to extract text information from the imported document.
You will still need to fill in all the metadata such as the document title,
year of publication, etc.

Deleting a document
-------------------

You can delete a document by going to the document Properties page and scrolling down to the **Danger Zone** section
and clicking the **Delete this document** button.

.. note:: You cannot delete a published document. Mark it as a draft first.

.. note:: Only users with the **Can delete document** permission can delete a document. An Administrator can change this for you in the Admin area.

.. note::

    If you delete a document by accident an administrator can undelete it for you.

    Administrators: visit ``/admin/indigo_api/document/`` and click on the document to recover, scroll down
    to find the **Deleted** checkbox, uncheck it and click **Save**.

.. _editing_metadata:

Editing Metadata
----------------

The metadata is important for describing the document and making it available through
the API.

.. image:: metadata.png

Basic Details
-------------

**Work** The details of the work this document is linked to. Change the work by clicking the button.

**Short title** is the generally used title of the document. Most pieces of legislation declare what the short title will be.

**Language** is the language of the document.

**Tags** is a free-form collection of tags for this document. Use tags to manage your documents during editing and even after publication. To add a new tag, click in the box, type a new tag and press enter or comma. You can add as many tabs as you like. To delete a tag, either backspace or click the **x** next to the tag's name.

**Stub document** indicates that the document doesn't have all its content yet. This is useful when other documents reference this one but no source is available
or the source has not been fully checked.

.. note::

    Administrators can add new countries, languages and document subtypes through the Admin interface. Click on your name in the top-right corner and choose **Site Settings**.

Draft and Publishing
....................

**Draft** controls whether the document is available publically. While you are editing the document, this should be **checked**. Outside users cannot see draft documents. Once a document is ready to be used by outside users, uncheck this box to indicate it is published.

.. note:: You cannot delete a published document. Mark it as a draft, first.

Amendments
..........

The Amendments section records amendments that have been applied to reach **this version of the document**. If you are not editing the latest
version of the document this must only include those amendments that have been applied to reach this point.

To record an amendment, you need the following information about the **amending document** (the document that caused the amendments to happen):

- the title
- date of publication (date at which the amendments took place)
- the FRBR URI of the document

If the amending document is already in the library, you can choose it from the list and have all these details filled in automatically.

To create a newly amended version of a document, edit the version just before the new amendments need to be applied and click **Clone Document**
to create a copy, and then edit that copy.

Attachments
...........

The Attachments section lets you attach files to your document. This is generally used to link a source PDF, Word or other file with your document, but you can upload any file you like. When creating a new document by importing a file, the file is automatically added as an attachment.

To upload a new file, click on **Attachments** and then click the **Choose Files** button.

You can change the name of an attachment by clicking the pencil (edit) icon.

Defined Terms Analysis
......................

Indigo can find defined terms in a document and associate occurrences of a term with its definition. It does this by looking for a section called ``Definitions`` or ``Interpretation`` and looking for sentences that look like definitions. It then looks through the document to find uses of any defined terms it has found.

To find and link terms, click **Analysis** and then **Find and link defined terms**.

When viewing a document, Indigo marks the definition of a defined term **in bold**.

.. important:: Defined terms are lost when a section is edited. It's best to find and link defined terms just before publishing a final document, or after doing a batch of updates.
