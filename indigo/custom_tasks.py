from collections import defaultdict

from indigo.plugins import LocaleBasedRegistry, LocaleBasedMatcher


class CustomTask(LocaleBasedMatcher):
    locale = (None, None, None)

    def setup(self, task):
        self.task = task

    def close_url(self):
        pass


class TaskRegistry(LocaleBasedRegistry):
    registry = defaultdict(dict)


tasks = TaskRegistry()
