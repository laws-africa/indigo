# coding=utf-8

from actstream import action
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import signals, Q
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.utils.functional import cached_property
import reversion.revisions
from reversion.models import Version
from cobalt import FrbrUri, RepealEvent

from indigo.plugins import plugins


class WorkQuerySet(models.QuerySet):
    def get_for_frbr_uri(self, frbr_uri):
        work = self.filter(frbr_uri=frbr_uri).first()
        if work is None:
            raise ValueError("Work for FRBR URI '%s' doesn't exist" % frbr_uri)
        return work


class WorkManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        # defer expensive or unnecessary fields
        return super(WorkManager, self) \
            .get_queryset() \
            .select_related('updated_by_user', 'created_by_user', 'country',
                            'country__country', 'locality', 'publication_document') \
            .prefetch_related('commencements')


class TaxonomyVocabulary(models.Model):
    authority = models.CharField(max_length=512, null=False, unique=True, blank=False, help_text="Organisation managing this taxonomy")
    name = models.CharField(max_length=512, null=False, unique=True, blank=False, help_text="Short name for this taxonomy, under this authority")
    slug = models.SlugField(null=False, unique=True, blank=False, help_text="Code used in the API")
    title = models.CharField(max_length=512, null=False, unique=True, blank=False, help_text="Friendly, full title for the taxonomy")

    class Meta:
        verbose_name = 'Taxonomy'
        verbose_name_plural = 'Taxonomies'
        ordering = ('title',)

    def __str__(self):
        return str(self.title)


class VocabularyTopic(models.Model):
    vocabulary = models.ForeignKey(TaxonomyVocabulary, related_name='topics', null=False, blank=False, on_delete=models.CASCADE)
    level_1 = models.CharField(max_length=512, null=False, blank=False)
    level_2 = models.CharField(max_length=512, null=True, blank=True, help_text='(optional)')

    class Meta:
        unique_together = ('level_1', 'level_2', 'vocabulary')
        ordering = ('level_1', 'level_2')

    @property
    def title(self):
        return ' / '.join(x for x in [self.level_1, self.level_2] if x)

    @property
    def slug(self):
        detail = '/'.join(x for x in [self.level_1, self.level_2] if x)
        return f'{self.vocabulary.slug}:{detail}'

    def __str__(self):
        return self.title

    @classmethod
    def get_topic(self, value):
        """ Get a taxonomy topic based on a string, such as lawsafrica-collections:level1[/level2]
        """
        if ':' in value:
            vocab, topic = value.split(':', 1)
            if '/' in topic:
                level_1, level_2 = topic.split('/', 1)
            else:
                level_1 = topic
                level_2 = None

            return VocabularyTopic.objects\
                .filter(vocabulary__slug=vocab, level_1=level_1, level_2=level_2)\
                .first()


class WorkMixin(object):
    """ Support methods that define behaviour for a work, independent of the database model.

    This makes it possible to change the underlying model class for a work, and then mixin
    this functionality.
    """
    _work_uri = None
    _repeal = None

    @property
    def work_uri(self):
        """ The FRBR Work URI as a :class:`FrbrUri` instance that uniquely identifies this work universally. """
        if self._work_uri is None:
            self._work_uri = FrbrUri.parse(self.frbr_uri)
        return self._work_uri

    @property
    def date(self):
        return self.work_uri.date

    @property
    def year(self):
        return self.work_uri.date.split('-', 1)[0]

    @property
    def number(self):
        return self.work_uri.number

    @property
    def nature(self):
        return self.work_uri.doctype

    @property
    def subtype(self):
        return self.work_uri.subtype

    @property
    def actor(self):
        return self.work_uri.actor

    @property
    def repeal(self):
        """ Repeal information for this work, as a :class:`cobalt.RepealEvent` object.
        None if this work hasn't been repealed.
        """
        if self._repeal is None:
            if self.repealed_by:
                self._repeal = RepealEvent(self.repealed_date, self.repealed_by.title, self.repealed_by.frbr_uri)
        return self._repeal

    @property
    def place(self):
        return self.locality or self.country

    @property
    def commencement_date(self):
        main = self.main_commencement
        if main:
            return main.date

    @property
    def commencement_note(self):
        main = self.main_commencement
        if main:
            return main.note

    @property
    def commencing_work(self):
        main = self.main_commencement
        if main:
            return main.commencing_work

    def amended(self):
        return self.amendments.exists()

    def most_recent_amendment_year(self):
        latest = self.amendments.order_by('-date').first()
        if latest:
            return latest.date.year

    def labeled_properties(self):
        props = self.place.settings.work_properties

        return sorted([{
            'label': props[key],
            'key': key,
            'value': val,
        } for key, val in self.properties.items() if val and key in props], key=lambda x: x['label'])

    def numbered_title(self):
        """ Return a formatted title using the number for this work, such as "Act 5 of 2009".
        This usually differs from the short title. May return None.
        """
        plugin = plugins.for_work('work-detail', self)
        if plugin:
            return plugin.work_numbered_title(self)

    def friendly_type(self):
        """ Return a friendly document type for this work, such as "Act" or "By-law".
        """
        plugin = plugins.for_work('work-detail', self)
        if plugin:
            return plugin.work_friendly_type(self)

    def expressions(self):
        """ A queryset of expressions of this work, in ascending expression date order.
        """
        from .documents import Document
        return Document.objects.undeleted().filter(work=self).order_by('expression_date')

    def initial_expressions(self):
        """ Queryset of expressions at initial publication date.
        """
        return self.expressions().filter(expression_date=self.publication_date)

    def possible_expression_dates(self):
        """ Return a list of dicts each describing a possible expression date on a work, in descending date order.
        Each has a date and specifies whether it is an amendment, consolidation, and/or initial expression.
        """
        initial = self.publication_date or self.commencement_date
        amendment_dates = [a.date for a in self.amendments.all()]
        consolidation_dates = [c.date for c in self.arbitrary_expression_dates.all()]
        all_dates = set(amendment_dates + consolidation_dates)
        dates = [
            {'date': date,
             'amendment': date in amendment_dates,
             'consolidation': date in consolidation_dates,
             'initial': date == initial}
            for date in all_dates
        ]

        if initial and initial not in all_dates:
            dates.append({
                'date': initial,
                'initial': True
            })

        dates.sort(key=lambda x: x['date'], reverse=True)
        return dates

    def all_provisions(self):
        # a list of the element ids of the earliest PiT (in whichever language) of a work
        # does not include Schedules as they don't have commencement dates
        first_expression = self.expressions().first()
        if first_expression:
            return first_expression.all_provisions()
        return None

    @cached_property
    def main_commencement(self):
        if self.commencements.exists():
            for c in list(self.commencements.all()):
                if c.main:
                    return c

    def first_commencement_date(self):
        first = self.commencements.first()
        if first:
            return first.date

    def all_commenceable_provisions(self, date=None):
        """ Return a list of TOCElement objects that can be commenced.
            If `date` is provided, only provisions in expressions up to and including that date are included.
        """
        # gather documents and sort so that we consider primary language documents first
        if date:
            documents = self.expressions().filter(expression_date__lte=date)
        else:
            documents = self.expressions().all()
        documents = sorted(documents, key=lambda d: 0 if d.language == self.country.primary_language else 1)

        # get all the docs and combine the TOCs, based on element IDs
        provisions = []
        id_set = set()
        for doc in documents:
            plugin = plugins.for_document('toc', doc)
            if plugin:
                plugin.insert_commenceable_provisions(doc, provisions, id_set)

        return provisions

    def all_uncommenced_provision_ids(self, date=None):
        commencements = self.commencements.all()
        # common case: one commencement that covers all provisions
        if any(c.all_provisions for c in commencements):
            return []

        commenced = [p for c in commencements for p in c.provisions]

        uncommenced_ids = []
        def add_to_uncommenced(p):
            if p.id not in commenced:
                uncommenced_ids.append(p.id)
            for c in p.children:
                add_to_uncommenced(c)

        for p in self.all_commenceable_provisions(date=date):
            add_to_uncommenced(p)

        return uncommenced_ids

    @property
    def commencements_count(self):
        """ The number of commencement objects, plus one if there are uncommenced provisions, on a work """
        commencements_count = len(self.commencements.all())
        if self.all_uncommenced_provision_ids():
            commencements_count += 1
        return commencements_count


class Work(WorkMixin, models.Model):
    """ A work is an abstract document, such as an act. It has basic metadata and
    allows us to track works that we don't have documents for, and provides a
    logical parent for documents, which are expressions of a work.
    """
    class Meta:
        permissions = (
            ('review_work', 'Can review work details'),
            ('bulk_add_work', 'Can import works in bulk'),
            ('bulk_export_work', 'Can export works in bulk'),
        )

    frbr_uri = models.CharField(max_length=512, null=False, blank=False, unique=True, help_text="Used globally to identify this work")
    """ The FRBR Work URI of this work that uniquely identifies it globally """

    title = models.CharField(max_length=1024, null=True, default='(untitled)')
    country = models.ForeignKey('indigo_api.Country', null=False, on_delete=models.PROTECT, related_name='works')
    locality = models.ForeignKey('indigo_api.Locality', null=True, blank=True, on_delete=models.PROTECT, related_name='works')

    # publication details
    publication_name = models.CharField(null=True, blank=True, max_length=255, help_text="Original publication, eg. government gazette")
    publication_number = models.CharField(null=True, blank=True, max_length=255, help_text="Publication's sequence number, eg. gazette number")
    publication_date = models.DateField(null=True, blank=True, help_text="Date of publication")

    assent_date = models.DateField(null=True, blank=True, help_text="Date signed by the president")

    commenced = models.BooleanField(null=False, default=False, help_text="Has this work commenced? (Date may be unknown)")

    # repeal information
    repealed_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, help_text="Work that repealed this work", related_name='repealed_works')
    repealed_date = models.DateField(null=True, blank=True, help_text="Date of repeal of this work")

    # optional parent work
    parent_work = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, help_text="Parent related work", related_name='child_works')

    stub = models.BooleanField(default=False, help_text="Stub works do not have content or points in time")

    # key-value pairs of extra data, using keys for this place from PlaceSettings.work_properties
    properties = JSONField(null=False, blank=True, default=dict)

    # taxonomies
    taxonomies = models.ManyToManyField(VocabularyTopic, related_name='works')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    updated_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

    objects = WorkManager.from_queryset(WorkQuerySet)()

    @property
    def locality_code(self):
        # Helper to get/set locality using the locality_code, used by the WorkSerializer.
        return self.locality.code

    @locality_code.setter
    def locality_code(self, value):
        if value:
            locality = self.country.localities.filter(code=value).first()
            if not locality:
                raise ValueError("No such locality for this country: %s" % value)
            self.locality = locality
        else:
            self.locality = None

    def clean(self):
        # validate and clean the frbr_uri
        try:
            frbr_uri = FrbrUri.parse(self.frbr_uri).work_uri(work_component=False)
        except ValueError:
            raise ValidationError("Invalid FRBR URI")

        # Assume frbr_uri starts with /akn; `rest` is everything after the country/locality, e.g.
        # in `/akn/za-wc/act/2000/12`, `rest` is `act/2000/12`.
        rest = frbr_uri.split('/', 3)[3]

        # force akn prefix, country and locality codes in frbr uri
        prefix = '/akn/' + self.country.code
        if self.locality:
            prefix = prefix + '-' + self.locality.code

        self.frbr_uri = f'{prefix}/{rest}'.lower()

    def save(self, *args, **kwargs):
        # prevent circular references
        if self.repealed_by == self:
            self.repealed_by = None
        if self.parent_work == self:
            self.parent_work = None

        if not self.repealed_by:
            self.repealed_date = None

        return super(Work, self).save(*args, **kwargs)

    def save_with_revision(self, user, comment=None):
        """ Save this work and create a new revision at the same time.
        """
        with reversion.revisions.create_revision():
            reversion.revisions.set_user(user)
            if comment:
                reversion.revisions.set_comment(comment)
            self.updated_by_user = user
            self.save()

    def can_delete(self):
        return (not self.document_set.undeleted().exists() and
                not self.child_works.exists() and
                not self.repealed_works.exists() and
                not self.commencements_made.exists() and
                not Amendment.objects.filter(Q(amending_work=self) | Q(amended_work=self)).exists())

    def create_expression_at(self, user, date, language=None):
        """ Create a new expression at a particular date.

        This uses an existing document at or before this date as a template, if available.
        """
        from .documents import Document, Attachment

        language = language or self.country.primary_language
        doc = Document(work=self)

        # most recent expression at or before this date
        template = self.document_set \
            .undeleted() \
            .filter(expression_date__lte=date, language=language) \
            .order_by('-expression_date') \
            .first()

        if template:
            doc.title = template.title
            doc.content = template.content

        doc.draft = True
        doc.language = language
        doc.expression_date = date
        doc.created_by_user = user
        doc.save()

        # copy over attachments to new expression
        attachments = Attachment.objects.filter(document=template)
        for attachment in attachments:
            attachment.pk = None
            attachment.document = doc
            attachment.file.save(attachment.filename, attachment.file)
            attachment.save()

        return doc

    def versions(self):
        """ Return a queryset of `reversion.models.Version` objects for
        revisions for this work, most recent first.
        """
        return Version.objects.get_for_object(self).select_related('revision', 'revision__user')

    def as_at_date(self):
        # the as-at date is the maximum of the most recent, published expression date,
        # and the place's as-at date.
        q = self.expressions().published().order_by('-expression_date').values('expression_date').first()

        dates = [
            (q or {}).get('expression_date'),
            self.place.settings.as_at_date,
        ]

        dates = [d for d in dates if d]
        if dates:
            return max(dates)

    def __str__(self):
        return '%s (%s)' % (self.frbr_uri, self.title)


@receiver(signals.post_save, sender=Work)
def post_save_work(sender, instance, **kwargs):
    """ Cascade changes to linked documents
    """
    if not kwargs['raw'] and not kwargs['created']:
        # cascade updates to ensure documents
        # pick up changes to inherited attributes
        for doc in instance.document_set.all():
            # forces call to doc.copy_attributes()
            doc.updated_by_user = instance.updated_by_user
            doc.save()

    # Send action to activity stream, as 'created' if a new work
    if kwargs['created']:
        action.send(instance.created_by_user, verb='created', action_object=instance,
                    place_code=instance.place.place_code)
    else:
        action.send(instance.updated_by_user, verb='updated', action_object=instance,
                    place_code=instance.place.place_code)


# version tracking
reversion.revisions.register(Work)


def publication_document_filename(instance, filename):
    return 'work-attachments/%s/publication-document' % (instance.work.id,)


class PublicationDocument(models.Model):
    work = models.OneToOneField(Work, related_name='publication_document', null=False, on_delete=models.CASCADE)
    # either file or trusted_url should be provided
    file = models.FileField(upload_to=publication_document_filename)
    trusted_url = models.URLField(null=True, blank=True)
    size = models.IntegerField(null=True)
    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def build_filename(self):
        # don't include /akn/ from FRBR URI in filename
        return f"{self.work.frbr_uri[5:].replace('/', '-')}-publication-document.pdf"

    def save(self, *args, **kwargs):
        self.filename = self.build_filename()
        return super(PublicationDocument, self).save(*args, **kwargs)


class Commencement(models.Model):
    """ The commencement details of (provisions of) a work,
    optionally performed by a commencing work or a provision of the work itself.
    """
    commenced_work = models.ForeignKey(Work, on_delete=models.CASCADE, null=False, help_text="Principal work being commenced", related_name="commencements")
    commencing_work = models.ForeignKey(Work, on_delete=models.SET_NULL, null=True, help_text="Work that provides the commencement date for the principal work", related_name="commencements_made")
    date = models.DateField(null=True, blank=True, help_text="Date of the commencement, or null if it is unknown")
    main = models.BooleanField(default=False, help_text="This commencement date is the date on which most of the provisions of the principal work come into force")
    all_provisions = models.BooleanField(default=False, help_text="All provisions of this work commenced on this date")
    note = models.TextField(max_length=1024, blank=True, null=True, help_text="Usually a reference to a provision of the commenced work or a commencing work, if there is a commencement but the date is open to interpretation")

    # list of the element ids of the provisions commenced, e.g. ["sec_2", "sec_4.3.list0.a"]
    provisions = JSONField(null=False, blank=False, default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    updated_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

    class Meta:
        ordering = ['date']
        unique_together = (('commenced_work', 'commencing_work', 'date'),)

    def rationalise(self, user):
        work = self.commenced_work
        if not work.commenced:
            work.commenced = True
        work.updated_by_user = user
        work.save()

    def expressions(self):
        """ The commenced work's documents (expressions) at this date.
        """
        return self.commenced_work.expressions().filter(expression_date=self.date)


@receiver(signals.post_save, sender=Commencement)
def post_save_commencement(sender, instance, **kwargs):
    # Send action to activity stream, as 'created' if a new commencement,
    if kwargs['created']:
        action.send(instance.created_by_user, verb='created', action_object=instance,
                    place_code=instance.commenced_work.place.place_code)
    else:
        action.send(instance.updated_by_user, verb='updated', action_object=instance,
                    place_code=instance.commenced_work.place.place_code)


class Amendment(models.Model):
    """ An amendment to a work, performed by an amending work.
    """
    amended_work = models.ForeignKey(Work, on_delete=models.CASCADE, null=False, help_text="Work amended.", related_name='amendments')
    amending_work = models.ForeignKey(Work, on_delete=models.CASCADE, null=False, help_text="Work making the amendment.", related_name='amendments_made')
    date = models.DateField(null=False, blank=False, help_text="Date of the amendment")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    updated_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

    class Meta:
        ordering = ['date']

    def expressions(self):
        """ The amended work's documents (expressions) at this date.
        """
        return self.amended_work.expressions().filter(expression_date=self.date)

    def can_delete(self):
        return not self.expressions().exists()


@receiver(signals.post_save, sender=Amendment)
def post_save_amendment(sender, instance, **kwargs):
    """ When an amendment is created, save any documents already at that date
    to ensure the details of the amendment are stashed correctly in each document.
    """
    if kwargs['created']:
        for doc in instance.amended_work.document_set.filter(expression_date=instance.date):
            # forces call to doc.copy_attributes()
            doc.updated_by_user = instance.created_by_user
            doc.save()

        # Send action to activity stream, as 'created' if a new amendment
        action.send(instance.created_by_user, verb='created', action_object=instance,
                    place_code=instance.amended_work.place.place_code)
    else:
        action.send(instance.updated_by_user, verb='updated', action_object=instance,
                    place_code=instance.amended_work.place.place_code)


class ArbitraryExpressionDate(models.Model):
    """ An arbitrary expression date not tied to an amendment, e.g. a consolidation date.
    """
    date = models.DateField(null=False, blank=False, help_text="Arbitrary date, e.g. consolidation date")
    description = models.TextField(null=True, blank=True)
    work = models.ForeignKey(Work, on_delete=models.CASCADE, null=False, help_text="Work", related_name="arbitrary_expression_dates")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    updated_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

    class Meta:
        unique_together = ('date', 'work')
        ordering = ['date']

    def expressions(self):
        """ The work's documents (expressions) at this date.
        """
        return self.work.expressions().filter(expression_date=self.date)

    def can_delete(self):
        return not self.expressions().exists()

    @property
    def amended_work(self):
        return self.work


@receiver(signals.post_save, sender=ArbitraryExpressionDate)
def post_save_arbitrary_expression_date(sender, instance, **kwargs):
    # Send action to activity stream, as 'created' if a new arbitrary expression date
    if kwargs['created']:
        action.send(instance.created_by_user, verb='created', action_object=instance,
                    place_code=instance.work.place.place_code)
    else:
        action.send(instance.updated_by_user, verb='updated', action_object=instance,
                    place_code=instance.work.place.place_code)


class Subtype(models.Model):
    name = models.CharField(max_length=1024, help_text="Name of the document subtype")
    abbreviation = models.CharField(max_length=20, help_text="Short abbreviation to use in FRBR URI. No punctuation.", unique=True)

    # cheap cache for subtypes, to avoid DB lookups
    _cache = {}

    class Meta:
        verbose_name = 'Document subtype'
        ordering = ('name',)

    def clean(self):
        if self.abbreviation:
            self.abbreviation = self.abbreviation.lower()

    def __str__(self):
        return '%s (%s)' % (self.name, self.abbreviation)

    @classmethod
    def for_abbreviation(cls, abbr):
        if not cls._cache:
            cls._cache = {s.abbreviation: s for s in cls.objects.all()}
        return cls._cache.get(abbr)


@receiver(signals.post_save, sender=Subtype)
def on_subtype_saved(sender, instance, **kwargs):
    # clear the subtype cache
    Subtype._cache = {}
