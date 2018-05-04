from __future__ import absolute_import

from indigo_analysis.registry import register_analyzer, LocaleBasedAnalyzer


class RefsRegistry(type):
    def __new__(cls, name, *args):
        newclass = super(RefsRegistry, cls).__new__(cls, name, *args)
        if name != 'BaseRefsFinder':
            register_analyzer('refs', newclass)
        return newclass


class BaseRefsFinder(LocaleBasedAnalyzer):
    """ Finds references to Acts in documents.

    Subclasses must implement `find_references_in_document`.
    """

    __metaclass__ = RefsRegistry

    def find_references_in_document(self, document):
        raise NotImplementedError()
