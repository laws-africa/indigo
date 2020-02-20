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


@register.simple_tag
def commenced_provisions_description(document, commencement, uncommenced=False):
    work = document.work
    if uncommenced:
        uncommenced_provisions = document.work.uncommenced_provisions()
        # TODO: same as below for uncommenced provisions
        return ', '.join([p.id for p in uncommenced_provisions])

    commenceable_provisions = work.commenceable_provisions()
    commenced_provisions = commencement.provisions
    runs = []
    current_run = []

    def end_current_run(run):
        if len(run) < 4:
            run = [f'{item["type"]} {item["num"]}' for item in run]
        else:
            run = [f'{run[0]["type"]} {run[0]["num"]}–{run[-1]["num"]}']
        runs.append(run)

    for i, p in enumerate(commenceable_provisions):
        if i == 0:
            if p.id in commenced_provisions:
                current_run.append({'type': p.type, 'num': p.num.split('.')[0] if p.num else ''})
        else:
            previous = commenceable_provisions[i - 1]
            if p.id not in commenced_provisions and previous.id in commenced_provisions:
                end_current_run(current_run)
                current_run = []
            elif p.id in commenced_provisions:
                if not current_run:
                    # new run
                    current_run = [{'type': p.type, 'num': p.num.split('.')[0] if p.num else ''}]
                elif p.type == previous.type:
                    # current run is safe to add to (same type)
                    current_run.append({'type': p.type, 'num': p.num.split('.')[0] if p.num else ''})
                else:
                    # current run is not safe to add to (different type)
                    end_current_run(current_run)
                    current_run = [{'type': p.type, 'num': p.num.split('.')[0] if p.num else ''}]
    # we've finished checking all commenceable provisions
    end_current_run(current_run)

    return ', '.join(', '.join(r) for r in runs)
