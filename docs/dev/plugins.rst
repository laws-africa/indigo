Plugins
=======

..
  TODO: update below if TocBuilder stops being a locale-based plugin.

Indigo uses plugins to allow specific functionality to be customised
for different countries, localities and languages. For example,
extracting a Table of Contents and automatically linking references
both use the plugin system. This means they can be adjusted to suit
different languages and references styles.

Locales
-------

Most plugins are locale-aware. That is, Indigo looks for a plugin implementation
that best matches the locale of a work or a document.

The locale is a tuple of strings ``(country, language, locality)``, such as
``('za', 'eng', None)``, where ``None`` is a wildcard that will match anything. The
tuple describes the locales to which the plugin applies. In this example, the
plugin applies to any work in South Africa (``za``) with an English (``eng``)
expression, and will match on any locality within South Africa (the last ``None``
item).

If there are multiple plugins with locales that match a document or work,
Indigo will use the one that most specifically matches it (i.e. has the fewest wildcards.)

Plugin registry
---------------

Plugins register themselves with the plugin registry for a certain
topic. The following plugin topics are understood by Indigo:

..
  TODO: update this list: add PDF exporter, bulk creator; potentially remove toc

* ``importer`` plugins import text from documents and mark them up with Akoma Ntoso. Usually extend :class:`indigo_api.importers.base.Importer`.
* ``publications`` plugins provide publication documents for works. Usually extend :class:`indigo.analysis.publications.base.BasePublicationFinder`.
* ``refs`` plugins automatically identify and markup references between works in the text of a document. Usually extend :class:`indigo.analysis.refs.base.BaseRefsFinder`.
* ``terms`` plugins automatically identify and markup defined terms in document markup. Usually extend :class:`indigo.analysis.terms.base.BaseTermsFinder`.
* ``toc`` plugins return a Table of Contents from document markup. Usually extend :class:`indigo.analysis.toc.base.TOCBuilderBase`.
* ``work-detail`` plugins return tradition-specific information for a work, such as numbered titles. Usually extend :class:`indigo.analysis.work_detail.base.BaseWorkDetail`.

Register a plugin using ``plugins.register(topic)`` and include a ``locale`` that describes which locales your plugin is specific to::

    from indigo.analysis.work_detail.base import BaseWorkDetail
    from indigo.plugins import plugins


    @plugins.register('work-detail')
    class CustomisedWorkDetail(BaseWorkDetail):
        locale = ('za', 'afr', None)
        ...

Fetching a plugin
-----------------

You can fetch a plugin for a work or a document using :meth:`~indigo.plugins.LocaleBasedRegistry.for_work`,
:meth:`~indigo.plugins.LocaleBasedRegistry.for_document`, or :meth:`~indigo.plugins.LocaleBasedRegistry.for_locale`
on the plugin registry, giving it a plugin topic and a work, document or locale::

    from indigo.plugins import plugins

    toc_builder = plugins.for_document('toc', document)
    if toc_builder:
        toc_builder.table_of_contents_for_document(document)

Custom tasks
------------

You can also create custom tasks using the plugin system. Custom tasks can provide
specific URLs for performing the task, control who can close a task, etc.

Indigo recognises a custom task using the ``Task.code`` attribute on the task. This
is an arbitrary string value which you provide when you register your custom task
with the registry.

Like plugins, tasks are also locale-specific so you can provide
locale-dependent implementations.  More than one custom task can be registered
for the same task code. Indigo will use the implementation with the closest locale match.

Register your task with the task system like this::

    from indigo.custom_tasks import CustomTask, tasks

    @tasks.register('my-custom-code')
    class MyCustomTask(CustomTask):
        locale = (None, None, None)

        def setup(self, task):
            self.task = task

When Indigo sees a task with a task ``code`` attribute, it will lookup the
custom task from the registry, create an instance, and call ``setup(task)``
with the ``task`` instance.

Loading plugins and custom tasks
--------------------------------

It's common to place your plugins in ``plugins.py`` and custom tasks in ``custom_tasks.py`` in your project directory. Then load those files in your Django ``apps.py`` when Django calls your app's ``ready()`` method::

    from django.apps import AppConfig


    class MyAppConfig(AppConfig):
        name = 'my_app'

        def ready(self):
            # ensure our plugins are pulled in
            import my_app.plugins
            import my_app.custom_tasks

Plugin API reference
--------------------

..
  TODO: update

.. autoclass:: indigo_api.importers.base.Importer
    :members:

.. autoclass:: indigo.analysis.publications.base.BasePublicationFinder
    :members:

.. autoclass:: indigo.analysis.refs.base.BaseRefsFinder
    :members:

.. autoclass:: indigo.analysis.terms.base.BaseTermsFinder
    :members:

.. autoclass:: indigo.analysis.toc.base.TOCBuilderBase
    :members:

.. autoclass:: indigo.analysis.work_detail.base.BaseWorkDetail
    :members:

.. autoclass:: indigo.analysis.work_detail.base.BaseWorkDetail
    :members:

.. autoclass:: indigo.plugins.LocaleBasedRegistry
    :members:
