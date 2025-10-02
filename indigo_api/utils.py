import hashlib
import logging

from django.template.loader import get_template, TemplateDoesNotExist
from functools import lru_cache
from django.contrib.postgres.search import Value, Func, SearchRank
from django.contrib.staticfiles.finders import find as find_static
from django.core.cache import cache
from django.db.models import TextField

from languages_plus.models import Language
from rest_framework.pagination import PageNumberPagination as BasePageNumberPagination

from indigo.analysis.differ import AKNHTMLDiffer


log = logging.getLogger(__name__)


@lru_cache()
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

    The following templates are looked for, in order. Note that place includes locality, and is only used
    if place != country (e.g. za-cpt vs za)

    * doctype-subtype-language-place
    * doctype-subtype-language-country
    * doctype-subtype-language
    * doctype-subtype-place
    * doctype-subtype-country
    * doctype-subtype
    * doctype-language-place
    * doctype-language-country
    * doctype-place
    * doctype-country
    * doctype-language
    * doctype
    * place
    * country
    * akn
    """
    uri = document.expression_uri
    doctype = uri.doctype
    language = uri.language
    country = uri.country
    place = uri.place
    subtype = uri.subtype

    options = []
    if subtype:
        if country != place:
            options.append('-'.join([doctype, subtype, language, place]))
        options.append('-'.join([doctype, subtype, language, country]))
        options.append('-'.join([doctype, subtype, language]))
        if country != place:
            options.append('-'.join([doctype, subtype, place]))
        options.append('-'.join([doctype, subtype, country]))
        options.append('-'.join([doctype, subtype]))

    if country != place:
        options.append('-'.join([doctype, language, place]))
    options.append('-'.join([doctype, language, country]))
    if country != place:
        options.append('-'.join([doctype, place]))
    options.append('-'.join([doctype, country]))
    options.append('-'.join([doctype, language]))
    options.append(doctype)
    if country != place:
        options.append(place)
    options.append(country)
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


async def adiff_html_str(old_html, new_html):
    """ Asynchronously compute the diff between two HTML strings, returning
    a string with the HTML diff.

    This uses caching based on the md5sum of the two strings.
    """
    md5_old = hashlib.md5(old_html.encode('utf-8')).hexdigest()
    md5_new = hashlib.md5(new_html.encode('utf-8')).hexdigest()
    cache_key = f"adiff_html_str-{md5_old}-{md5_new}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    result = await AKNHTMLDiffer().adiff_html_str(old_html, new_html)
    cache.set(cache_key, result, timeout=7 * 86400)  # cache for 7 days

    return result
