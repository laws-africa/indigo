from __future__ import absolute_import

from indigo_analysis.registry import register_analyzer, LocaleBasedAnalyzer


class TermsRegistry(type):
    def __new__(cls, name, *args):
        newclass = super(TermsRegistry, cls).__new__(cls, name, *args)
        if name != 'BaseTermsFinder':
            register_analyzer('terms', newclass)
        return newclass


class BaseTermsFinder(LocaleBasedAnalyzer):
    """ Finds references to defined terms in documents.

    Subclasses must implement `find_terms_in_document`.
    """

    __metaclass__ = TermsRegistry

    def find_terms_in_document(self, document):
        raise NotImplementedError()
