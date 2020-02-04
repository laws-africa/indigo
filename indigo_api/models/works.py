# coding=utf-8
from itertools import chain, groupby

from actstream import action
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import signals, Q
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from django.utils.functional import cached_property
import reversion.revisions
import reversion.models
from cobalt.act import FrbrUri, RepealEvent

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
                            'country__country', 'locality', 'publication_document')


class TaxonomyVocabulary(models.Model):
    authority = models.CharField(max_length=30, null=False, unique=True, blank=False, help_text="Organisation managing this taxonomy")
    name = models.CharField(max_length=30, null=False, unique=True, blank=False, help_text="Short name for this taxonomy, under this authority")
    slug = models.SlugField(null=False, unique=True, blank=False, help_text="Code used in the API")
    title = models.CharField(max_length=30, null=False, unique=True, blank=False, help_text="Friendly, full title for the taxonomy")

    class Meta:
        verbose_name = 'Taxonomy'
        verbose_name_plural = 'Taxonomies'

    def __str__(self):
        return str(self.title)


class VocabularyTopic(models.Model):
    vocabulary = models.ForeignKey(TaxonomyVocabulary, related_name='topics', null=False, blank=False, on_delete=models.CASCADE)
    level_1 = models.CharField(max_length=30, null=False, blank=False)
    level_2 = models.CharField(max_length=30, null=True, blank=True, help_text='(optional)')

    class Meta:
        unique_together = ('level_1', 'level_2', 'vocabulary')

    def __str__(self):
        if self.level_2:
            return '%s / %s' % (self.level_1, self.level_2)
        else:
            return self.level_1


class Work(models.Model):
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

    _work_uri = None
    _repeal = None

    @property
    def work_uri(self):
        """ The FRBR Work URI as a :class:`FrbrUri` instance that uniquely identifies this work universally. """
        if self._work_uri is None:
            self._work_uri = FrbrUri.parse(self.frbr_uri)
        return self._work_uri

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

    @property
    def repeal(self):
        """ Repeal information for this work, as a :class:`cobalt.act.RepealEvent` object.
        None if this work hasn't been repealed.
        """
        if self._repeal is None:
            if self.repealed_by:
                self._repeal = RepealEvent(self.repealed_date, self.repealed_by.title, self.repealed_by.frbr_uri)
        return self._repeal

    @property
    def place(self):
        return self.locality or self.country

    @cached_property
    def commencement_date(self):
        return self.main_commencement_date()

    @cached_property
    def commencing_work(self):
        return self.main_commencing_work()

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

    def clean(self):
        # validate and clean the frbr_uri
        try:
            frbr_uri = FrbrUri.parse(self.frbr_uri).work_uri(work_component=False)
        except ValueError:
            raise ValidationError("Invalid FRBR URI")

        # force country and locality codes in frbr uri
        prefix = '/' + self.country.code
        if self.locality:
            prefix = prefix + '-' + self.locality.code

        self.frbr_uri = ('%s/%s' % (prefix, frbr_uri.split('/', 2)[2])).lower()

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
                not [c for c in self.commencements.all() if c.commencing_work] and
                not Amendment.objects.filter(Q(amending_work=self) | Q(amended_work=self)).exists())

    def create_expression_at(self, user, date, language=None):
        """ Create a new expression at a particular date.

        This uses an existing document at or before this date as a template, if available.
        """
        from .documents import Document

        language = language or self.country.primary_language
        doc = Document()

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
        doc.work = self
        doc.created_by_user = user
        doc.save()

        return doc

    def expressions(self):
        """ A queryset of expressions of this work, in ascending expression date order.
        """
        from .documents import Document

        return Document.objects.undeleted().filter(work=self).order_by('expression_date')

    def initial_expressions(self):
        """ Queryset of expressions at initial publication date.
        """
        return self.expressions().filter(expression_date=self.publication_date)

    def versions(self):
        """ Return a queryset of `reversion.models.Version` objects for
        revisions for this work, most recent first.
        """
        content_type = ContentType.objects.get_for_model(self)
        return reversion.models.Version.objects \
            .select_related('revision', 'revision__user') \
            .filter(content_type=content_type) \
            .filter(object_id_int=self.id) \
            .order_by('-id')

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

    def amendments_with_initial_and_arbitrary(self):
        """ Return a list of Amendment and ArbitraryExpressionDate objects, including a fake one at the end
        that represents the initial point-in-time. This will include multiple
        objects at the same date, if there were multiple amendments at the same date.
        """
        initial = ArbitraryExpressionDate(work=self, date=self.publication_date or self.commencement_date)
        initial.initial = True
        amendments_expressions = list(self.amendments.all()) + list(self.arbitrary_expression_dates.all())
        amendments_expressions.sort(key=lambda x: x.date)

        if initial.date:
            if not amendments_expressions or amendments_expressions[0].date != initial.date:
                amendments_expressions.insert(0, initial)

            if amendments_expressions[0].date == initial.date:
                amendments_expressions[0].initial = True

        amendments_expressions.reverse()
        return amendments_expressions

    def points_in_time(self):
        """ Return a list of dicts describing a point in time, one entry for each date,
        in descending date order.
        """
        amendments_expressions = self.amendments_with_initial_and_arbitrary()
        pits = []

        for date, group in groupby(amendments_expressions, key=lambda x: x.date):
            group = list(group)
            pits.append({
                'date': date,
                'initial': any(getattr(a, 'initial', False) for a in group),
                'amendments': group,
                'expressions': set(chain(*(a.expressions().all() for a in group))),
            })

        return pits

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

    def all_provisions(self):
        # a list of the element ids of the earliest PiT (in whichever language) of a work
        # does not include Schedules as they don't have commencement dates
        first_expression = self.expressions().first()
        if first_expression:
            return first_expression.all_provisions()
        return None

    def main_commencement(self):
        main = self.commencements.filter(main=True).first()
        if main:
            return main
        return None

    def main_commencement_date(self):
        main = self.main_commencement()
        if main:
            return main.date
        return None

    def main_commencing_work(self):
        main = self.main_commencement()
        if main:
            return main.commencing_work
        return None

    def first_commencement_date(self):
        first = self.commencements.first()
        if first:
            return first.date
        return None

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
        return '{}-publication-document.pdf'.format(self.work.frbr_uri[1:].replace('/', '-'))

    def save(self, *args, **kwargs):
        self.filename = self.build_filename()
        return super(PublicationDocument, self).save(*args, **kwargs)


class Commencement(models.Model):
    """ The commencement details of (provisions of) a work,
    optionally performed by a commencing work or a provision of the work itself.

    """
    commenced_work = models.ForeignKey(Work, on_delete=models.CASCADE, null=False, help_text="Principal work being commenced", related_name="commencements")
    commencing_work = models.ForeignKey(Work, on_delete=models.CASCADE, null=True, help_text="Work that provides the commencement date for the principal work", related_name="commencements_made")
    date = models.DateField(null=True, blank=True, help_text="Date of the commencement, or null if it is unknown")
    main = models.BooleanField(default=False, help_text="This commencement date is the date on which most of the provisions of the principal work come into force")
    all_provisions = models.BooleanField(default=False, help_text="All provisions of this work commenced on this date")

    # list of the element ids of the provisions commenced, e.g. ["section-2", "section-4.3.list0.a"]
    provisions = JSONField(null=False, blank=False, default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    updated_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

    class Meta:
        ordering = ['date']
        unique_together = (('commenced_work', 'commencing_work', 'date'),)

    def is_only_commencement(self):
        """ checks that the current commencement object is the only one associated with this commenced work,
        as well as that it's the main one and that it commences all provisions.
        """
        return bool(
            self.main is True and
            self.all_provisions is True and
            not self.other_commencements().exists()
        )

    def other_commencements(self):
        return Commencement.objects.filter(commenced_work=self.commenced_work).exclude(pk=self.pk)

    def save(self, *args, **kwargs):
        # ensure only one commencement with main=True on commenced work
        existing_main_commencement = self.commenced_work.main_commencement()
        if existing_main_commencement and existing_main_commencement != self:
            self.main = False

        # ensure only one commencement with all_provisions=True on commenced work
        existing_all_provisions_commencement = self.commenced_work.commencements.filter(all_provisions=True).first()
        if existing_all_provisions_commencement and existing_all_provisions_commencement != self:
            self.all_provisions = False

        return super(Commencement, self).save(*args, **kwargs)


class UncommencedProvisions(models.Model):
    """ The details of uncommenced provisions of a work
    """
    commenced_work = models.OneToOneField(Work, on_delete=models.CASCADE, null=False, help_text="Principal work with uncommenced provisions", related_name="uncommenced_provisions")
    all_provisions = models.BooleanField(default=False, help_text="All provisions of this work are uncommenced")

    # list of the element ids of the uncommenced provisions, e.g. ["section-2", "section-4.3.list0.a"]
    provisions = JSONField(null=False, blank=False, default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    updated_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

    def save(self, *args, **kwargs):
        # ensure only one commencement / uncommencement with all_provisions=True on commenced work
        if self.all_provisions:
            existing_all_provisions_commencement = self.commenced_work.commencements.filter(all_provisions=True).first()
            if existing_all_provisions_commencement:
                self.all_provisions = False

        return super(UncommencedProvisions, self).save(*args, **kwargs)


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
