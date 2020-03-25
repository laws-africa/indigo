from indigo.analysis.work_detail.base import BaseWorkDetail
from indigo.plugins import plugins
from indigo_api.models import Subtype


@plugins.register('work-detail')
class WorkDetailZA(BaseWorkDetail):
    locale = ('za', None, None)
    """ Locale for this object, as a tuple: (country, language, locality). None matches anything."""
    no_numbered_title_subtypes = ['by-law', 'mo']


@plugins.register('work-detail')
class WorkDetailZAAfr(WorkDetailZA):
    locale = ('za', 'afr', None)
    """ Locale for this object, as a tuple: (country, language, locality). None matches anything."""

    def work_numbered_title(self, work):
        if not super().work_numbered_title(work):
            return

        number = work.number.upper()
        work_type = self.work_friendly_type(work)
        return f'{work_type} {number} van {work.year}'

    def work_friendly_type(self, work):
        """ Return a friendly document type for this work, such as "Wet" or "General Notice".
        """
        uri = work.work_uri
        subtypes = {
            'gn': 'Goewermentskennisgewing',
            'genn': 'Algemene Kennisgewing',
            'p': 'Proklamasie',
        }

        if uri.subtype:
            # use the subtype full name, if we have it
            subtype = subtypes.get(uri.subtype)
            return subtype or uri.subtype.upper()

        return 'Wet'
