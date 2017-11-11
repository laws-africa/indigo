from languages_plus.models import Language
from django.utils import lru_cache


@lru_cache.lru_cache()
def language3_to_2(code):
    """ Convert a 3-letter language code to a 2-letter version.
    Returns None if no match is found.
    """
    try:
        return Language.objects.get_by_code(code).iso_639_1
    except Language.DoesNotExist:
        return None
