# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from indigo.analysis.toc.base import TOCBuilderBase
from indigo.plugins import plugins


@plugins.register('toc')
class TOCBuilderPL(TOCBuilderBase):
    locale = ('pl', 'pol', None)

    toc_elements = ["article", "chapter", "conclusions", "coverpage", "division", "paragraph", "preamble", "preface", "section", "subdivision"]
    toc_non_unique_components = ['chapter', 'subdivision', 'paragraph']

    titles = {
        'article': lambda t: 'Art. %s' % t.num + (' - %s' % t.heading if t.heading else ''),
        'chapter': lambda t: 'Rozdział  %s' % t.num + (' - %s' % t.heading if t.heading else ''),
        'division': lambda t: 'Dział  %s' % t.num + (' - %s' % t.heading if t.heading else ''),
        'paragraph': lambda t: t.num,
        'section': lambda t: '§ %s' % t.num,
    }
