from django.utils.translation import ugettext as _

from indigo_analysis.toc.base import TOCBuilderBase
from indigo.plugins import plugins


def section_title(item):
    if item.heading:
        title = item.heading
        if item.num:
            title = item.num + ' ' + title
    else:
        title = _('Section')
        if item.num:
            title = title + ' ' + item.num
    return title


@plugins.register('toc')
class TOCBuilderZA(TOCBuilderBase):
    locale = ('za', None, None)

    toc_elements = ['coverpage', 'preface', 'preamble', 'part', 'chapter', 'section', 'conclusions']
    toc_non_unique_components = ['chapter', 'part']

    titles = {
        'chapter': lambda t: _('Chapter') + ' %s' % t.num + (' - %s' % t.heading if t.heading else ''),
        'part': lambda t: _('Part') + ' %s' % t.num + (' - %s' % t.heading if t.heading else ''),
        'section': section_title,
    }
