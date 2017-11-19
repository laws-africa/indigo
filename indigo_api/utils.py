from django.utils import lru_cache
from django.utils.translation import override, ugettext as _
from django.contrib.postgres.search import Value, Func, SearchRank
from django.db.models import TextField

from languages_plus.models import Language
from rest_framework.pagination import PageNumberPagination


# Ensure that these translations are included by makemessages
_('Act')
_('Chapter')
_('Part')
_('Section')
_('Government Notice')
_('By-law')


@lru_cache.lru_cache()
def language3_to_2(code):
    """ Convert a 3-letter language code to a 2-letter version.
    Returns None if no match is found.
    """
    try:
        return Language.objects.get_by_code(code).iso_639_1
    except Language.DoesNotExist:
        return None


def localize_toc(toc, language):
    """ Localize a document's TOC.
    """
    def localize(item):
        if item.title:
            item.title = friendly_toc_title(item)
        for kid in item.children or []:
            localize(kid)

    with override(language):
        for t in toc:
            localize(t)

    return toc


def friendly_toc_title(item):
    """ Build a friendly title for a table of contents element, based on heading names etc.
    """
    if item.type in ['chapter', 'part']:
        title = _(item.type.capitalize())
        if item.num:
            title += ' ' + item.num
        if item.heading:
            title += ' - ' + item.heading

    elif item.type == 'section':
        if item.heading:
            title = item.heading
            if item.num:
                title = item.num + ' ' + title
        else:
            title = _('Section')
            if item.num:
                title = title + ' ' + item.num

    elif item.heading:
        title = item.heading

    else:
        title = _(item.type.capitalize())
        if item.num:
            title += u' ' + item.num

    return title


class Headline(Func):
    """ Helper class for using the `ts_headline` postgres function when executing
    search queries.
    """
    function = 'ts_headline'

    def __init__(self, field, query, config=None, options=None, **extra):
        expressions = [field, query]
        if config:
            expressions.insert(0, Value(config))
        if options:
            expressions.append(Value(options))
        extra.setdefault('output_field', TextField())
        super(Headline, self).__init__(*expressions, **extra)


class SearchPagination(PageNumberPagination):
    page_size = 20


class SearchRankCD(SearchRank):
    # this takes proximity into account
    function = 'ts_rank_cd'
