from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag(takes_context=True)
def work_resolver_url(context, work):
    if not work:
        return None

    if not isinstance(work, str):
        frbr_uri = work.frbr_uri
    else:
        frbr_uri = work

    if context.get('media_resolver_use_akn_prefix') and not frbr_uri.startswith('/akn'):
        # for V2 APIs, prefix FRBR URI with /akn
        frbr_uri = '/akn' + frbr_uri

    return context.get('resolver_url', settings.RESOLVER_URL) + frbr_uri


def make_beautiful(provisions, commenceable_provisions):
    runs = []
    current_run = []
    previous = None

    def add_to_current(element):
        current_run.append({'type': element.type, 'num': element.num.strip('.')})

    def end_current():
        if len(current_run) < 3:
            run = [f'{item["type"]} {item["num"]}' for item in current_run]
        else:
            run = [f'{current_run[0]["type"]} {current_run[0]["num"]}–{current_run[-1]["num"]}']
        runs.append(run)
        return []

    for p in commenceable_provisions:
        if p.id in provisions:
            if not previous:
                add_to_current(p)
                previous = p
                continue

            if previous.id in provisions and previous.type != p.type:
                # current run is not safe to add to (different type)
                current_run = end_current()
            add_to_current(p)

        elif previous and previous.id in provisions:
            current_run = end_current()

        previous = p

    # we've finished checking all commenceable provisions; add the last group
    # (but not if it's empty)
    if current_run:
        end_current()

    return ', '.join(', '.join(p) for p in runs)


@register.simple_tag
def commenced_provisions_description(document, commencement, uncommenced=False):
    if uncommenced:
        provisions = [p.id for p in document.uncommenced_provisions()]
    else:
        provisions = commencement.provisions

    commenceable_provisions = document.commenceable_provisions()

    return make_beautiful(provisions, commenceable_provisions)


@register.simple_tag
def commencements_relevant_at_date(document):
    return document.work.commencements_relevant_at_date(date=document.expression_date)
