from collections import defaultdict

from indigo.plugins import LocaleBasedRegistry, LocaleBasedMatcher


class CustomTask(LocaleBasedMatcher):
    """ Parent class for providing custom functionality for Indigo tasks.

    To create a custom task, create a subclass of CustomTask and register
    it with the tasks registry.
    """

    locale = (None, None, None)
    """ Locale for this object, as a tuple: (country, language, locality). None matches anything."""

    def setup(self, task):
        self.task = task

    def close_url(self):
        pass


class TaskRegistry(LocaleBasedRegistry):
    registry = defaultdict(dict)


tasks = TaskRegistry()
