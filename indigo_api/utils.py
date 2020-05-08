import logging

from django.template.loader import get_template, TemplateDoesNotExist
from django.utils import lru_cache
from django.contrib.postgres.search import Value, Func, SearchRank
from django.contrib.staticfiles.finders import find as find_static
from django.db.models import TextField

from languages_plus.models import Language
from rest_framework.pagination import PageNumberPagination as BasePageNumberPagination


log = logging.getLogger(__name__)


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


def filename_candidates(document, prefix='', suffix=''):
    """ Candidate files to use for this document.

    This takes into account the country, type, subtype and language of the document,
    providing a number of opportunities to adjust the rendering logic.

    The following templates are looked for, in order:

    * doctype-subtype-language-country
    * doctype-subtype-language
    * doctype-subtype-country
    * doctype-subtype
    * doctype-language-country
    * doctype-country
    * doctype-language
    * doctype
    * akn
    """
    uri = document.expression_uri
    doctype = uri.doctype
    language = uri.language
    country = uri.country
    subtype = uri.subtype

    options = []
    if subtype:
        options.append('-'.join([doctype, subtype, language, country]))
        options.append('-'.join([doctype, subtype, language]))
        options.append('-'.join([doctype, subtype, country]))
        options.append('-'.join([doctype, subtype]))

    options.append('-'.join([doctype, language, country]))
    options.append('-'.join([doctype, country]))
    options.append('-'.join([doctype, language]))
    options.append(doctype)
    options.append('akn')

    return [prefix + f + suffix for f in options]


def find_best_static(candidates, actual=True):
    """ Return the first static file that exists given a list of candidate files.
    """
    for option in candidates:
        log.debug("Looking for %s" % option)
        fname = find_static(option)
        if fname:
            log.debug("Using %s" % fname)
            return fname if actual else option


def find_best_template(candidates):
    """ Return the first template that exists given a list of candidate files.
    """
    for option in candidates:
        try:
            log.debug("Looking for %s" % option)
            if get_template(option):
                log.debug("Using %s" % option)
                return option
        except TemplateDoesNotExist:
            pass
