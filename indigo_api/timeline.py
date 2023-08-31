from dataclasses import dataclass, field

from django.utils.formats import date_format
from django.utils.translation import gettext as _


@dataclass
class TimelineEvent:
    event_type: str = ''
    description: str = ''
    by_frbr_uri: str = ''
    by_title: str = ''
    note: str = ''
    related: object = None


@dataclass
class TimelineCommencementEvent(TimelineEvent):
    event_type: str = 'commencement'
    subtype: str = ''
    by_work: object = None
    date: object = None


@dataclass
class TimelineEntry:
    date: object = None
    initial: bool = False
    events: list[TimelineEvent] = field(default_factory=list)

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
                'event_type': event.event_type,
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


def get_timeline(work):
    """ Returns a list of TimelineEvent objects, each describing a date on the timeline of a work.
    """
    from indigo_api.models import Amendment
    entries = []

    all_amendments = work.amendments.all()
    all_commencements = work.commencements.all()
    all_consolidations = work.arbitrary_expression_dates.all()

    amendment_dates = [c.date for c in all_amendments]
    commencement_dates = [c.date for c in all_commencements]
    consolidation_dates = [c.date for c in all_consolidations]
    other_dates = [work.assent_date, work.publication_date, work.repealed_date]
    # don't include None
    all_dates = [e for e in amendment_dates + commencement_dates + consolidation_dates + other_dates if e]
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

        # even though the timeline is given in reverse chronological order,
        # each date on the timeline is described in regular order: assent first, repeal last

        # assent
        if date == work.assent_date:
            entry.events.append(TimelineEvent(event_type='assent', description=_('Assented to')))
        # publication
        if date == work.publication_date:
            entry.events.append(TimelineEvent(event_type='publication', description=_('Published')))

        # amendment
        for amendment in amendments:
            description = TimelineEvent(
                event_type='amendment', description=_('Amended by'), related=amendment,
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
                event_type='consolidation', description=_('Consolidation'), related=consolidation))
        # repeal
        if date == work.repealed_date:
            entry.events.append(TimelineEvent(
                event_type='repeal', description=_('Repealed by'), by_frbr_uri=work.repealed_by.frbr_uri,
                by_title=work.repealed_by.title))

        entries.append(entry)

    # reverse chronological order
    entries.sort(key=lambda x: x.date, reverse=True)

    return entries


def get_serialized_timeline(work):
    return [entry.serialized() for entry in get_timeline(work)]
