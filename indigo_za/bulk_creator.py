# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from indigo.analysis.bulk_creator.base import BaseBulkCreator
from indigo.plugins import plugins


@plugins.register('bulk-creator')
class BulkCreatorZA(BaseBulkCreator):
    """ Create works in bulk from a google sheets spreadsheet for the South African tradition.
    """
    locale = ('za', None, None)

