from django.utils import lru_cache
from django.contrib.postgres.search import Value, Func, SearchRank
from django.db.models import TextField

from languages_plus.models import Language
from rest_framework.pagination import PageNumberPagination as BasePageNumberPagination


@lru_cache.lru_cache()
def language3_to_2(code):
    """ Convert a 3-letter language code to a 2-letter version.
    Returns None if no match is found.
    """
    try:
        return Language.objects.get_by_code(code).iso_639_1
    except Language.DoesNotExist:
        return None


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


class SearchRankCD(SearchRank):
    # this takes proximity into account
    function = 'ts_rank_cd'


class PageNumberPagination(BasePageNumberPagination):
    page_size = 500
    page_size_query_param = 'page_size'
    max_page_size = 500


class SearchPagination(PageNumberPagination):
    page_size = 20
