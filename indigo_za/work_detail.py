from indigo.analysis.work_detail.base import BaseWorkDetail
from indigo.plugins import plugins


@plugins.register('work-detail')
class WorkDetailZA(BaseWorkDetail):
    def work_numbered_title(self, work):
        uri = work.work_uri

        # by-laws don't have numbered titles
        if uri.subtype == 'by-law':
            return None

        return super(WorkDetailZA, self).work_numbered_title(work)
