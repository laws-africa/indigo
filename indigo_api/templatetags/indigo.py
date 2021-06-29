from django import template
from django.conf import settings

register = template.Library()


class Beautifier:
    cap_types = ['part', 'chapter']

    def __init__(self, commenced):
        self.commenced = commenced

    def decorate_provisions(self, provisions, assess_against):
        # TODO: check all these are still needed
        def assess(p):
            for c in p.children:
                assess(c)

            # do this here for all provisions
            p.num = p.num.strip('.')

            # when self.commenced is True, assess_against is the list of commenced provision ids
            # when self.commenced is False, assess_against is the list of uncommenced provision ids
            p.commenced = self.commenced if p.id in assess_against else not self.commenced

            p.last_node = not p.children

            p.all_descendants_commenced = all(
                c.commenced and
                (c.all_descendants_commenced or c.last_node)
                for c in p.children
            ) if p.children else False

            p.some_descendants_commenced = any(
                c.commenced or c.some_descendants_commenced
                for c in p.children
            )

            p.contains_basic_unit = any(
                c.basic_unit or c.contains_basic_unit
                for c in p.children
            )

            # e.g. Subpart I contains sections 1 to 3, all of which are fully commenced
            # empty list passed to all() returns True
            p.fully_commenced_container = all(
                c.fully_commenced_container or
                (c.basic_unit and c.commenced and (c.all_descendants_commenced or c.last_node))
                for c in p.children
            ) if p.children else False

            # e.g. Part A contains Subparts I to IV, one or more of which are fully commenced containers
            p.contains_fully_commenced_container = any(
                c.contains_fully_commenced_container or
                c.fully_commenced_container
                for c in p.children
            )
            # e.g. Subpart I contains sections 1 to 3, all of which are fully uncommenced
            # empty list passed to all() returns True
            p.fully_uncommenced_container = all(
                c.fully_uncommenced_container or
                (c.basic_unit and not c.commenced and not c.some_descendants_commenced)
                for c in p.children
            ) if p.children else False

            p.contains_fully_uncommenced_container = any(
                c.contains_fully_uncommenced_container or
                c.fully_uncommenced_container
                for c in p.children
            )

            # fully (un)commenced Chapter or Part (skip intervening containers if all are commenced)
            p.full_container = p.contains_basic_unit and p.commenced == self.commenced and \
                               (p.all_descendants_commenced if self.commenced else not p.some_descendants_commenced)
            p.partial_container = p.contains_fully_commenced_container if self.commenced \
                else p.contains_fully_uncommenced_container

            # all children are the opposite
            p.lonely_container = p.commenced == self.commenced and p.contains_basic_unit and (not p.some_descendants_commenced if self.commenced else p.all_descendants_commenced)
            p.contains_lonely_container = any(c.lonely_container or c.contains_lonely_container for c in p.children)

            p.in_part_container = p.commenced == self.commenced and p.contains_basic_unit and (
                not p.all_descendants_commenced if self.commenced else p.some_descendants_commenced
            )
            p.contains_in_part_container = any(c.contains_in_part_container or c.in_part_container for c in p.children)

        for p in provisions:
            assess(p)

        return provisions

    def add_to_run(self, p, run):
        typ = p.type.capitalize() if p.type in self.cap_types else p.type
        # start a new run if this type is different
        new_run = typ not in [r['type'] for r in run] if run else False
        run.append({'type': typ, 'num': p.num, 'new_run': new_run})

    def stringify_run(self, run):
        # first (could be only) item, e.g. 'section 1'
        run_str = f"{run[0]['type']} {run[0]['num']}"
        # common case: e.g. section 1–5 (all the same type)
        if len(run) > 1 and not any(r['new_run'] for r in run):
            run_str += f"–{run[-1]['num']}"

        # e.g. section 1–3, article 1–2, regulation 1
        elif len(run) > 1:
            # get all of the first group, e.g. section
            first_type = [r for r in run if r['type'] == run[0]['type']]
            run_str += f"–{first_type[-1]['num']}" if len(first_type) > 1 else ''

            # get all e.g. articles, then all e.g. regulations
            for subsequent_type in [r['type'] for r in run if r['new_run']]:
                this_type = [r for r in run if r['type'] == subsequent_type]
                run_str += f", {subsequent_type} {this_type[0]['num']}"
                run_str += f"–{this_type[-1]['num']}" if len(this_type) > 1 else ''

        return run_str

    def add_all_basics(self, p):
        """ Adds a description of all basic units in a container to the container's `num`.
        e.g. Part A's `num`: 'A' --> 'A (section 1–3)'
        """
        # get all the basic units in the container
        basics = []
        def check_for_basics(p):
            if p.basic_unit:
                self.add_to_run(p, basics)
            for c in p.children:
                check_for_basics(c)
        for c in p.children:
            check_for_basics(c)

        p.num += f' ({self.stringify_run(basics)})' if basics else ''

    def add_to_current(self, p, all_basic_units=False):
        if all_basic_units:
            # num becomes more descriptive
            self.add_all_basics(p)
        self.add_to_run(p, self.current_run)

    def end_current(self):
        if self.current_run:
            self.runs.append(self.stringify_run(self.current_run))
            self.current_run = []
            self.previous_in_run = False

    def start_processing(self, p):
        if self.commenced:
            # ignore p only if it's fully uncommenced
            return p.commenced or p.some_descendants_commenced
        # ignore p only if it's fully commenced
        return not p.commenced or (p.children and not p.all_descendants_commenced)

    def process_basic_unit(self, p):
        """ Adds the subprovisions that have also (not) commenced to the basic unit's `num`,
        unless the entire provision is (un)commenced.
        e.g. section 2's `num`: '2' --> '2(1), 2(3), 2(4)'
        e.g. section 1's `num`: '1' --> '1(1)(a)(ii), 1(1)(a)(iii), 1(1)(c), 1(2)'
        """
        subs_to_add = []
        def check_subs(p):
            if self.commenced:
                # only drill down if the whole basic unit isn't commenced
                return not p.all_descendants_commenced
            # only drill down if the whole basic unit isn't uncommenced
            return p.some_descendants_commenced

        def stop_drilling(p):
            if self.commenced:
                # stop looking if the subprovision is fully commenced or is commenced and the last node,
                # or is the last commenced node
                return p.commenced and ((p.all_descendants_commenced or p.last_node) or not p.some_descendants_commenced)
            # stop looking if the subprovision is fully uncommenced or is uncommenced and the last node,
            # or is the last uncommenced node
            return not p.commenced and (
                (not p.some_descendants_commenced or p.last_node) or p.all_descendants_commenced
            )

        def keep_drilling(p):
            if self.commenced:
                # keep looking if a fully commenced subprovision hasn't been found yet
                return p.some_descendants_commenced
            # keep looking if a fully uncommenced subprovision hasn't been found yet
            return not p.all_descendants_commenced

        def add_to_subs(p, prefix):
            if stop_drilling(p):
                # go no further down but do prefix with all parent nums
                subs_to_add.append(f'{prefix}{p.num}')
            elif keep_drilling(p):
                for c in p.children:
                    add_to_subs(c, prefix + p.num)

        if check_subs(p):
            for c in p.children:
                add_to_subs(c, p.num)

        p.num = ', '.join(subs_to_add) if subs_to_add else p.num
        self.add_to_current(p)

    def process_provision(self, p):
        if self.start_processing(p):
            # e.g. a fully un/commenced Chapter or Part: Chapter 1 (sections 1–5)
            if p.full_container:
                self.add_to_current(p, all_basic_units=True)
                self.end_current()
            # e.g. a Chapter that contains a fully un/commenced Part: Chapter 1, Part A (sections 1–3)
            # (the part after the comma will be caught by full_container on the next iteration)
            # if e.g. 'Chapter 1' is given explicitly, add 'in part'
            elif p.partial_container or p.contains_in_part_container:
                if p.commenced == self.commenced:
                    p.num += ' (in part)'
                self.add_to_current(p)
            # e.g. a Part that has all uncommenced children but is itself commenced on this date
            elif p.lonely_container or p.in_part_container:
                p.num += ' (in part)'
                self.add_to_current(p)
                self.end_current()
            # e.g. section with subsections
            elif p.basic_unit:
                self.process_basic_unit(p)
                self.previous_in_run = True
            # lonely subprovision, e.g. Chapter 1 item (a)
            elif not p.contains_basic_unit and p.commenced == self.commenced:
                # TODO: deal with nested lonely subprovisions
                self.add_to_current(p)
                self.previous_in_run = True

            # keep going?
            if not (p.full_container or p.basic_unit):
                for c in p.children:
                    self.process_provision(c)

        elif self.previous_in_run:
            self.end_current()

    def make_beautiful(self, provisions):
        self.current_run = []
        self.runs = []
        self.previous_in_run = False

        for p in provisions:
            self.process_provision(p)

        self.end_current()

        # TODO: only join on ; between certain types of runs (TBD)
        return '; '.join(p for p in self.runs)


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
    if uncommenced:
        provision_ids = document.uncommenced_provision_ids()
    else:
        provision_ids = commencement.provisions

    beautifier = Beautifier(commenced=not uncommenced)
    # decorate the ToC with useful information
    provisions = beautifier.decorate_provisions(document.commenceable_provisions(), provision_ids)
    return beautifier.make_beautiful(provisions)


@register.simple_tag
def commencements_relevant_at_date(document):
    return document.commencements_relevant_at_expression_date()
