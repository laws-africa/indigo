from indigo.analysis.work_detail.base import BaseWorkDetail
from indigo.plugins import plugins


@plugins.register('work-detail')
class WorkDetailZA(BaseWorkDetail):
    locale = ('za', None, None)
    """ Locale for this object, as a tuple: (country, language, locality). None matches anything."""

    def work_numbered_title(self, work):
        uri = work.work_uri

        # by-laws don't have numbered titles
        if uri.subtype == 'by-law':
            return None

        return super(WorkDetailZA, self).work_numbered_title(work)
