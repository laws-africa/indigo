from indigo_analysis.registry import register_analyzer
from indigo_analysis.toc.base import TOCBuilderBase


def section_title(item):
    if item.heading:
        title = item.heading
        if item.num:
            title = item.num + ' ' + title
    else:
        title = 'Section'
        if item.num:
            title = title + ' ' + item.num
    return title


class TOCBuilderZA(TOCBuilderBase):
    locale = ('za', None, None)

    toc_elements = ['coverpage', 'preface', 'preamble', 'part', 'chapter', 'section', 'conclusions']
    toc_non_unique_components = ['chapter', 'part']

    titles = {
        'chapter': lambda t: 'Chapter %s' % t.num + (' - %s' % t.heading if t.heading else ''),
        'part': lambda t: 'Part %s' % t.num + (' - %s' % t.heading if t.heading else ''),
        'section': section_title,
    }

register_analyzer('toc', TOCBuilderZA)
