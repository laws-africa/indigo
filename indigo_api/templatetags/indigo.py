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


def make_beautiful(work, provisions):
    commenceable_provisions = work.commenceable_provisions()
    runs = []
    current_run = []

    def add_to_current(element, run):
        run.append({'type': element.type, 'num': element.num.strip('.')[0]})
        return run

    def end_current(run):
        if len(run) < 4:
            run = [f'{item["type"]} {item["num"]}' for item in run]
        else:
            run = [f'{run[0]["type"]} {run[0]["num"]}–{run[-1]["num"]}']
        runs.append(run)
        return []

    for i, p in enumerate(commenceable_provisions):
        if i > 0:
            previous = commenceable_provisions[i - 1]

        if p.id in provisions:
            if i == 0:
                current_run = add_to_current(p, current_run)
                continue

            if previous.id in provisions and previous.type != p.type:
                # current run is not safe to add to (different type)
                current_run = end_current(current_run)

            current_run = add_to_current(p, current_run)

        elif i > 0 and previous.id in provisions:
            current_run = end_current(current_run)

    # we've finished checking all commenceable provisions; add the last group
    # (but not if it's empty)
    if current_run:
        end_current(current_run)

    return runs


@register.simple_tag
def commenced_provisions_description(work, commencement, uncommenced=False):
    if uncommenced:
        provisions = [p.id for p in work.uncommenced_provisions()]
    else:
        provisions = commencement.provisions

    return ', '.join(', '.join(p) for p in make_beautiful(work, provisions))
