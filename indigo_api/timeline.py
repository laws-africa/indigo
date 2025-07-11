from dataclasses import dataclass, field
from django.db.models import TextChoices
from django.utils.formats import date_format
from django.utils.translation import gettext as _

from indigo.plugins import plugins


class TimelineEventType(TextChoices):
    AMENDMENT = 'amendment'
    ASSENT = 'assent'
    COMMENCEMENT = 'commencement'
    CONSOLIDATION = 'consolidation'
    PUBLICATION = 'publication'
    REPEAL = 'repeal'
    CHAPTER = 'chapter'


@dataclass
class TimelineEvent:
    type: TimelineEventType = ''
    description: str = ''
    by_frbr_uri: str = ''
    by_title: str = ''
    note: str = ''
    related: object = None


@dataclass
class TimelineCommencementEvent(TimelineEvent):
    type: str = TimelineEventType.COMMENCEMENT
    subtype: str = ''
    by_work: object = None
    date: object = None


@dataclass
class TimelineEntry:
    date: object = None
    initial: bool = False
    events: list = field(default_factory=list)

    def serialized(self):
        """ This differs from what we get from asdict:
            - date is stringified
            - we don't include all fields
        """
        entry = {
            'date': f'{self.date}',
            'events': [],
        }

        for event in self.events:
            entry['events'].append({
                'type': event.type,
                'description': event.description,
                'by_frbr_uri': event.by_frbr_uri,
                'by_title': event.by_title,
                'note': event.note,
            })

        return entry


def describe_single_commencement(commencement, with_date=True, friendly_date=True):
    description = TimelineCommencementEvent(subtype='single', related=commencement)

    if commencement.note:
        description.note = _('Note: %(note)s') % {'note': commencement.note}

    if commencement.commencing_work:
        description.by_frbr_uri = commencement.commencing_work.frbr_uri
        description.by_title = commencement.commencing_work.title
        description.by_work = commencement.commencing_work

    commencement_date = commencement.date
    if commencement_date:
        description.date = commencement_date
        if friendly_date:
            commencement_date = date_format(commencement_date, 'j E Y')

    if with_date and commencement_date:
        # with a date and a commencing work
        if commencement.commencing_work:
            description.description = _('Commenced on %(date)s by') % {'date': commencement_date}

        # with a date, without a commencing work
        else:
            description.description = _('Commenced on %(date)s') % {'date': commencement_date}

    # without a date, with a commencing work
    elif commencement.commencing_work:
        description.description = _('Commenced by')

    # without a date or a commencing work
    else:
        description.description = _('Commenced')

    return description


def describe_repeal(work, with_date=True, friendly_date=True):
    event = TimelineEvent(TimelineEventType.REPEAL, note=work.repealed_note)

    repealed_date = work.repealed_date
    if with_date and friendly_date:
        repealed_date = date_format(work.repealed_date, 'j E Y')

    if work.repealed_by:
        event.by_frbr_uri = work.repealed_by.frbr_uri
        event.by_title = work.repealed_by.title
        if with_date:
            event.description = _('%(verbed)s on %(date)s by') % {
                'verbed': _(work.repealed_verb).capitalize(),
                'date': repealed_date,
            }
        else:
            event.description = _('%(verbed)s by') % {
                'verbed': _(work.repealed_verb).capitalize(),
            }
    else:
        if with_date:
            event.description = _('%(verbed)s on %(date)s') % {
                'verbed': _(work.repealed_verb).capitalize(),
                'date': repealed_date,
            }
        else:
            event.description = _(work.repealed_verb).capitalize()

    return event


def describe_publication_event(work, with_date=True, friendly_date=True, placeholder=False):
    """ Based on the information available, return a TimelineEvent describing the publication document for a work.
        If `placeholder` is True, return a minimum placeholder string as the TimelineEvent's `description`.
        Otherwise, only return a TimelineEvent at all if at least one piece of publication information is available.
    """
    event = TimelineEvent(TimelineEventType.PUBLICATION)

    name = work.publication_name
    number = work.publication_number
    publication_date = work.publication_date

    if with_date and publication_date:
        if friendly_date:
            publication_date = date_format(publication_date, 'j E Y')

        if name and number:
            # Published in Government Gazette 12345 on 1 January 2009
            event.description = _('Published in %(name)s %(number)s on %(date)s') % {
                'name': name, 'number': number, 'date': publication_date
            }
        elif name or number:
            # Published in Government Gazette on 1 January 2009; or
            # Published in 12345 on 1 January 2009
            event.description = _('Published in %(name)s on %(date)s') % {
                'name': name or number, 'date': publication_date
            }
        else:
            # Published on 1 January 2009
            event.description = _('Published on %(date)s') % {
                'date': publication_date
            }

    elif name and number:
        # Published in Government Gazette 12345
        event.description = _('Published in %(name)s %(number)s') % {
            'name': name, 'number': number
        }

    elif name or number:
        # Published in Government Gazette; or
        # Published in 12345
        event.description = _('Published in %(name)s') % {
            'name': name or number
        }

    elif placeholder:
        event.description = _('Published')

    # don't return anything if there's no description
    if event.description:
        return event


def get_timeline(work, only_approved_events=False):
    """ Returns a list of TimelineEvent objects, each describing a date on the timeline of a work.
    """
    from indigo_api.models import Amendment
    entries = []

    # chapter numbers
    plugin = plugins.for_work('work-detail', work)

    all_amendments = (
        work.amendments.approved() if only_approved_events else work.amendments.all()
    ).select_related("amending_work")
    all_commencements = (
        work.commencements.approved() if only_approved_events else work.commencements.all()
    ).select_related("commencing_work")
    # consolidations can't be approved or not, as there's no related work
    all_consolidations = work.arbitrary_expression_dates.all()
    all_chapter_numbers = work.chapter_numbers.all()
    repealed_date = work.repealed_date
    if only_approved_events and work.repealed_by and work.repealed_by.work_in_progress:
        repealed_date = None

    amendment_dates = [c.date for c in all_amendments]
    commencement_dates = [c.date for c in all_commencements]
    consolidation_dates = [c.date for c in all_consolidations]
    chapter_dates = [c.validity_start_date for c in all_chapter_numbers]
    other_dates = [work.assent_date, work.publication_date, repealed_date]
    # don't include None
    all_dates = [e for e in amendment_dates + commencement_dates + consolidation_dates + chapter_dates + other_dates if e]
    all_dates = set(all_dates)

    # the initial date is the publication date, or the earliest of the consolidation and commencement dates, or None
    initial = work.publication_date
    if not initial and any(commencement_dates + consolidation_dates):
        initial = min(d for d in commencement_dates + consolidation_dates if d)

    for date in all_dates:
        entry = TimelineEntry(date=date, initial=date == initial)
        amendments = [a for a in all_amendments if a.date == date]
        if len(amendments) > 1:
            amendments = Amendment.order_further(amendments)
        commencements = [c for c in all_commencements if c.date == date]
        consolidations = [c for c in all_consolidations if c.date == date]
        chapter_numbers = [c for c in all_chapter_numbers if c.validity_start_date == date]

        # even though the timeline is given in reverse chronological order,
        # each date on the timeline is described in regular order: assent first, repeal last

        # chapter number (start of validity)
        for chapter_number in chapter_numbers:
            entry.events.append(TimelineEvent(
                TimelineEventType.CHAPTER,
                description=f'{plugin.chapter_number_name(chapter_number)} {chapter_number.number}',
                note=chapter_number.revision_name))

        # assent
        if date == work.assent_date:
            entry.events.append(TimelineEvent(TimelineEventType.ASSENT, description=_('Assented to')))
        # publication
        if date == work.publication_date:
            entry.events.append(describe_publication_event(work, with_date=False, placeholder=True))

        # amendment
        for amendment in amendments:
            description_description = _('Revised by') if amendment.verb == 'revised' else _('Amended by')
            description = TimelineEvent(
                TimelineEventType.AMENDMENT, description=description_description, related=amendment,
                by_frbr_uri=amendment.amending_work.frbr_uri,
                by_title=amendment.amending_work.title)

            # look for a commencement by the amending work at this date, include its note
            commencements_by_amending_work = [c for c in commencements if c.commencing_work == amendment.amending_work]
            # there can only ever be one commencement by the same work on the same date,
            # so the list will have a len of 0 or 1
            for c in commencements_by_amending_work:
                if c.note:
                    description.note = _('Commencement note: %(note)s') % {'note': c.note}
                # don't process the commencement
                commencements.pop(commencements.index(c))

            entry.events.append(description)

        # commencement
        for commencement in commencements:
            entry.events.append(describe_single_commencement(commencement, with_date=False))
        # consolidation
        for consolidation in consolidations:
            entry.events.append(TimelineEvent(
                TimelineEventType.CONSOLIDATION, description=_('Consolidation'), related=consolidation))
        # repeal
        if date == work.repealed_date and repealed_date:
            entry.events.append(describe_repeal(work, with_date=False))

        entries.append(entry)

    # reverse chronological order
    entries.sort(key=lambda x: x.date, reverse=True)

    return entries


def get_serialized_timeline(work):
    return [entry.serialized() for entry in get_timeline(work, only_approved_events=True)]
