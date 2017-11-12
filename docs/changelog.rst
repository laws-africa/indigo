Changelog
=========

3.0 (?)
-------

* FEATURE: support images in documents
* FEATURE: download as XML
* FEATURE: annotations/comments on documents
* FEATURE: download documents as ZIP archives
* You can now highlight lines of text in the editor and transform them into a table, using the Edit > Insert Table menu item.
* Edit menu with Find, Replace, Insert Table, Insert Image, etc.
* Presence indicators for other users editing the same document
* The LIME editor has been removed

2.0 (6 April 2017)
------------------

* Upgraded to Django 1.10
* Upgraded a number of dependencies to support Django 1.10
* FEATURE: significantly improved mechanism for maintaining amended versions of documents
* FEATURE: you can now edit tables directly inline in a document
* FEATURE: quickly edit a document section without having to open it via the TOC
* FEATURE: support for newlines in tables
* FEATURE: improved document page layout
* FEATURE: pre-loaded set of publication names per country
* Assent and commencement notices are no longer H3 elements, so PDFs don't include them in their TOCs. #28
* FIX: bug when saving an edited section
* FIX: ensure TOC urls use expression dates
* FIX: faster document saving

After upgrading to this version, you **must** run migrations::

    python manage.py migrate

We also recommend updating the list of countries::

    python manage.py update_countries_plus

1.1 (2016-12-19)
----------------

* First tagged release
