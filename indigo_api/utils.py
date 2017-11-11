from django.utils import lru_cache
from django.utils.translation import override, ugettext as _
from languages_plus.models import Language


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


# Ensure that these translations are included by makemessages
_('Act')
_('Chapter')
_('Part')
_('Section')
_('Government Notice')
_('By-law')
