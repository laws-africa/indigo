import os
import logging
import re
import datetime

from django.conf import settings
from django.db import models
from django.db.models import signals, Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import SearchVectorField
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
import arrow
from taggit.managers import TaggableManager
import reversion.revisions
import reversion.models

from countries_plus.models import Country as MasterCountry
from languages_plus.models import Language as MasterLanguage

from cobalt.act import Act, FrbrUri, RepealEvent, AmendmentEvent, datestring

from indigo.plugins import plugins

log = logging.getLogger(__name__)


class Language(models.Model):
    """ The languages available in the UI. They aren't enforced by the API.
    """
    language = models.OneToOneField(MasterLanguage, on_delete=models.CASCADE)

    class Meta:
        ordering = ['language__name_en']

    @property
    def code(self):
        """ 3 letter language code.
        """
        return self.language.iso_639_2B

    def __unicode__(self):
        return unicode(self.language)

    @classmethod
    def for_code(cls, code):
        return cls.objects.get(language__iso_639_2B=code)


class Country(models.Model):
    """ The countries available in the UI. They aren't enforced by the API.
    """
    country = models.OneToOneField(MasterCountry, on_delete=models.CASCADE)
    primary_language = models.ForeignKey(Language, on_delete=models.PROTECT, null=False, related_name='+', help_text='Primary language for this country')

    class Meta:
        ordering = ['country__name']
        verbose_name_plural = 'Countries'

    @property
    def code(self):
        return self.country.iso.lower()

    @property
    def name(self):
        return self.country.name

    def as_json(self):
        return {
            'name': self.name,
            'localities': {loc.code: loc.name for loc in self.localities.all()},
            'publications': [pub.name for pub in self.publication_set.all()],
        }

    def work_locality(self, work):
        return self.localities.filter(code=work.locality).first()

    def __unicode__(self):
        return unicode(self.country.name)

    @classmethod
    def for_frbr_uri(cls, frbr_uri):
        return cls.for_code(frbr_uri.country)

    @classmethod
    def for_code(cls, code):
        return cls.objects.get(country__pk=code.upper())


class Locality(models.Model):
    """ The localities available in the UI. They aren't enforced by the API.
    """
    country = models.ForeignKey(Country, null=False, on_delete=models.CASCADE, related_name='localities')
    name = models.CharField(max_length=512, null=False, blank=False, help_text="Local name of this locality")
    code = models.CharField(max_length=100, null=False, blank=False, help_text="Unique code of this locality (used in the FRBR URI)")

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Localities'
        unique_together = (('country', 'code'),)

    def __unicode__(self):
        return unicode(self.name)

    @classmethod
    def for_work(cls, work):
        if work.locality:
            return work.country.work_locality(work)


class WorkQuerySet(models.QuerySet):
    def get_for_frbr_uri(self, frbr_uri):
        work = self.filter(frbr_uri=frbr_uri).first()
        if work is None:
            raise ValueError("Work for FRBR URI '%s' doesn't exist" % frbr_uri)
        return work


class WorkManager(models.Manager):
    def get_queryset(self):
        # defer expensive or unnecessary fields
        return super(WorkManager, self)\
            .get_queryset()\
            .prefetch_related('country', 'country__country')


class Work(models.Model):
    """ A work is an abstract document, such as an act. It has basic metadata and
    allows us to track works that we don't have documents for, and provides a
    logical parent for documents, which are expressions of a work.
    """
    class Meta:
        permissions = (
            ('review_work', 'Can review work details'),
            ('view_work', 'Can list and view work details'),
        )

    frbr_uri = models.CharField(max_length=512, null=False, blank=False, unique=True, help_text="Used globally to identify this work")
    """ The FRBR Work URI of this work that uniquely identifies it globally """

    title = models.CharField(max_length=1024, null=True, default='(untitled)')
    country = models.ForeignKey(Country, null=False, on_delete=models.PROTECT)

    # publication details
    publication_name = models.CharField(null=True, blank=True, max_length=255, help_text="Original publication, eg. government gazette")
    publication_number = models.CharField(null=True, blank=True, max_length=255, help_text="Publication's sequence number, eg. gazette number")
    publication_date = models.DateField(null=True, blank=True, help_text="Date of publication")

    commencement_date = models.DateField(null=True, blank=True, help_text="Date of commencement unless otherwise specified")
    assent_date = models.DateField(null=True, blank=True, help_text="Date signed by the president")

    # repeal information
    repealed_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, help_text="Work that repealed this work", related_name='repealed_works')
    repealed_date = models.DateField(null=True, blank=True, help_text="Date of repeal of this work")

    # optional parent work
    parent_work = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, help_text="Parent related work", related_name='child_works')

    # optional work that determined the commencement date of this work
    commencing_work = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, help_text="Date that marked this work as commenced", related_name='commenced_works')

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
    def locality(self):
        return self.work_uri.locality

    @property
    def repeal(self):
        """ Repeal information for this work, as a :class:`cobalt.act.RepealEvent` object.
        None if this work hasn't been repealed.
        """
        if self._repeal is None:
            if self.repealed_by:
                self._repeal = RepealEvent(self.repealed_date, self.repealed_by.title, self.repealed_by.frbr_uri)
        return self._repeal

    def clean(self):
        # force country code in frbr uri
        self.frbr_uri = '/%s%s' % (self.country.code, self.frbr_uri[3:])
        # ensure the frbr uri is lowercased
        self.frbr_uri = self.frbr_uri.lower()

    def save(self, *args, **kwargs):
        # prevent circular references
        if self.commencing_work == self:
            self.commencing_work = None
        if self.repealed_by == self:
            self.repealed_by = None
        if self.parent_work == self:
            self.parent_work = None

        if not self.repealed_by:
            self.repealed_date = None

        return super(Work, self).save(*args, **kwargs)

    def can_delete(self):
        return (not self.document_set.undeleted().exists() and
                not self.child_works.exists() and
                not self.repealed_works.exists() and
                not self.commenced_works.exists() and
                not Amendment.objects.filter(Q(amending_work=self) | Q(amended_work=self)).exists())

    def create_expression_at(self, date, language=None):
        """ Create a new expression at a particular date.

        This uses an existing document at or before this date as a template, if available.
        """
        language = language or self.country.primary_language
        doc = Document()

        # most recent expression at or before this date
        template = self.document_set\
            .undeleted()\
            .filter(expression_date__lte=date, language=language)\
            .order_by('-expression_date')\
            .first()

        if template:
            doc.title = template.title
            doc.content = template.content

        doc.draft = True
        doc.language = language
        doc.expression_date = date
        doc.work = self
        doc.save()

        return doc

    def expressions(self):
        """ A queryset of expressions of this work, in ascending expression date order.
        """
        return self.document_set.undeleted().order_by('expression_date')

    def initial_expressions(self):
        """ Queryset of expressions at initial publication date.
        """
        return self.expressions().filter(expression_date=self.publication_date)

    def versions(self):
        """ Return a queryset of `reversion.models.Version` objects for
        revisions for this work, most recent first.
        """
        content_type = ContentType.objects.get_for_model(self)
        return reversion.models.Version.objects\
            .prefetch_related('revision', 'revision__user')\
            .filter(content_type=content_type)\
            .filter(object_id_int=self.id)\
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

    def amendments_with_initial(self):
        """ Return a list of Amendment objects, including a fake one at the end
        that represents the initial point-in-time.
        """
        initial = Amendment(amended_work=self, date=self.publication_date)
        initial.initial = True

        amendments = list(self.amendments.all())
        amendments.insert(0, initial)
        amendments.reverse()

        return amendments

    def __unicode__(self):
        return '%s (%s)' % (self.frbr_uri, self.title)


@receiver(signals.post_save, sender=Work)
def post_save_work(sender, instance, **kwargs):
    """ Cascade (soft) deletes to linked documents
    """
    if not kwargs['raw'] and not kwargs['created']:
        # cascade updates to ensure documents
        # pick up changes to inherited attributes
        for doc in instance.document_set.all():
            # forces call to doc.copy_attributes()
            doc.save()


class Amendment(models.Model):
    """ An amendment to a work, performed by an amending work.
    """
    amended_work = models.ForeignKey(Work, on_delete=models.CASCADE, null=False, help_text="Work amended.", related_name='amendments')
    amending_work = models.ForeignKey(Work, on_delete=models.CASCADE, null=False, help_text="Work making the amendment.", related_name='+')
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
        return self.amended_work.document_set.undeleted().filter(expression_date=self.date)

    def can_delete(self):
        return not self.expressions().exists()


@receiver(signals.post_save, sender=Amendment)
@receiver(signals.pre_delete, sender=Amendment)
def post_save_amendment(sender, instance, **kwargs):
    """ When an amendment is saved, update the expressions of the amended
    work to ensure the details of the amendment (ie. the date) are stashed
    correctly in the document.
    """
    if not kwargs.get('raw'):
        for doc in instance.amended_work.document_set.all():
            # forces call to doc.copy_attributes()
            doc.save()


class DocumentManager(models.Manager):
    def get_queryset(self):
        # defer expensive or unnecessary fields
        return super(DocumentManager, self)\
            .get_queryset()\
            .prefetch_related('work')\
            .defer("search_text", "search_vector")


class DocumentQuerySet(models.QuerySet):
    def undeleted(self):
        return self.filter(deleted=False)

    def published(self):
        return self.filter(draft=False)

    def no_xml(self):
        return self.defer('document_xml')

    def latest_expression(self):
        """ Select only the most recent expression for documents with the same frbr_uri.
        """
        return self.distinct('frbr_uri').order_by('frbr_uri', '-expression_date')

    def get_for_frbr_uri(self, frbr_uri):
        """ Find a single document matching the FRBR URI.

        Raises ValueError if any part of the URI isn't valid.

        See http://docs.oasis-open.org/legaldocml/akn-nc/v1.0/cs01/akn-nc-v1.0-cs01.html#_Toc492651893
        """
        query = self.filter(frbr_uri=frbr_uri.work_uri())

        # filter on language
        if frbr_uri.language:
            query = query.filter(language__language__iso_639_2B=frbr_uri.language)

        # filter on expression date
        expr_date = frbr_uri.expression_date

        if not expr_date:
            # no expression date is equivalent to the "current" version, at time of retrieval
            expr_date = ':' + datetime.date.today().strftime("%Y-%m-%d")

        try:
            if expr_date == '@':
                # earliest document
                query = query.order_by('expression_date')

            elif expr_date[0] == '@':
                # document at this date
                query = query.filter(expression_date=arrow.get(expr_date[1:]).date())

            elif expr_date[0] == ':':
                # latest document at or before this date
                query = query\
                    .filter(expression_date__lte=arrow.get(expr_date[1:]).date())\
                    .order_by('-expression_date')

            else:
                raise ValueError("The expression date %s is not valid" % expr_date)

        except arrow.parser.ParserError:
            raise ValueError("The expression date %s is not valid" % expr_date)

        obj = query.first()
        if obj is None:
            raise ValueError("Document doesn't exist")

        if obj and frbr_uri.language and obj.language.code != frbr_uri.language:
            raise ValueError("The document %s exists but is not available in the language '%s'"
                             % (frbr_uri.work_uri(), frbr_uri.language))

        return obj


class Document(models.Model):
    class Meta:
        permissions = (
            ('publish_document', 'Can publish and edit non-draft documents'),
            ('view_published_document', 'Can view publish documents through the API'),
        )

    objects = DocumentManager.from_queryset(DocumentQuerySet)()

    work = models.ForeignKey(Work, on_delete=models.CASCADE, db_index=True, null=False)
    """ The work this document is an expression of. Details from the work will be inherited by this document.
    This is not exposed externally. Instead, the document is automatically linked to the appropriate
    work using the FRBR URI.

    You cannot create a document that has an FRBR URI that doesn't match a work.
    """

    frbr_uri = models.CharField(max_length=512, null=False, blank=False, default='/', help_text="Used globally to identify this work")
    """ The FRBR Work URI of this document that uniquely identifies it globally """

    title = models.CharField(max_length=1024, null=False)

    """ The 3-letter ISO-639-2 language code of this document """
    language = models.ForeignKey(Language, null=False, on_delete=models.PROTECT, help_text="Language this document is in.")
    draft = models.BooleanField(default=True, help_text="Drafts aren't available through the public API")
    """ Is this a draft? """

    document_xml = models.TextField(null=True, blank=True)
    """ Raw XML content of the entire document """

    # Date from the FRBRExpression element. This is either the publication date or the date of the last
    # amendment. This is used to identify this particular version of this work, so is stored in the DB.
    expression_date = models.DateField(null=False, blank=False, help_text="Date of publication or latest amendment")

    stub = models.BooleanField(default=False, help_text="Is this a placeholder document without full content?")
    """ Is this a stub without full content? """

    deleted = models.BooleanField(default=False, help_text="Has this document been deleted?")

    # freeform tags via django-taggit
    tags = TaggableManager()

    # for full text search
    search_text = models.TextField(null=True, blank=True)
    search_vector = SearchVectorField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    updated_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

    # caching attributes
    _expression_uri = None

    @property
    def doc(self):
        """ The wrapped `an.act.Act` that this document works with. """
        if not getattr(self, '_doc', None):
            self._doc = self._make_act(self.document_xml)
        return self._doc

    @property
    def content(self):
        """ Alias for `document_xml` """
        return self.document_xml

    @content.setter
    def content(self, value):
        """ The correct way to update the raw XML of the document. This will re-parse the XML
        and other attributes -- such as the document title and FRBR URI based on the XML. """
        self.reset_xml(value, from_model=False)

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
    def country(self):
        return self.work_uri.country

    @property
    def locality(self):
        return self.work_uri.locality

    def amendments(self):
        if self.expression_date:
            return [a for a in self.work.amendments.all() if a.date <= self.expression_date]
        else:
            return []

    def amendment_events(self):
        return [
            AmendmentEvent(a.date, a.amending_work.title, a.amending_work.frbr_uri)
            for a in self.amendments()]

    @property
    def repeal(self):
        return self.work.repeal

    @property
    def work_uri(self):
        """ The FRBR Work URI as a :class:`FrbrUri` instance that uniquely identifies this work universally. """
        return self.work.work_uri

    @property
    def expression_uri(self):
        """ The FRBR Expression URI as a :class:`FrbrUri` instance that uniquely identifies this expression universally. """
        if self._expression_uri is None:
            self._expression_uri = self.work_uri.clone()
            self._expression_uri.language = self.language.code
            if self.expression_date:
                self._expression_uri.expression_date = '@' + datestring(self.expression_date)
        return self._expression_uri

    @property
    def commencement_date(self):
        return self.work.commencement_date

    @property
    def assent_date(self):
        return self.work.assent_date

    @property
    def publication_name(self):
        return self.work.publication_name

    @property
    def publication_number(self):
        return self.work.publication_number

    @property
    def publication_date(self):
        return self.work.publication_date

    def save(self, *args, **kwargs):
        self.copy_attributes()
        self.update_search_text()
        return super(Document, self).save(*args, **kwargs)

    def save_with_revision(self, user):
        """ Save this document and create a new revision at the same time.
        """
        with reversion.revisions.create_revision():
            reversion.revisions.set_user(user)
            self.save()

    def copy_attributes(self, from_model=True):
        """ Copy attributes from the model into the XML document, or reverse
        if `from_model` is False. """

        if from_model:
            self.copy_attributes_from_work()

            self.doc.title = self.title
            self.doc.frbr_uri = self.frbr_uri
            self.doc.language = self.language.code

            self.doc.work_date = self.doc.publication_date
            self.doc.expression_date = self.expression_date or self.doc.publication_date or arrow.now()
            self.doc.manifestation_date = self.updated_at or arrow.now()
            self.doc.publication_number = self.publication_number
            self.doc.publication_name = self.publication_name
            self.doc.publication_date = self.publication_date
            self.doc.repeal = self.work.repeal

        else:
            self.title = self.doc.title
            self.frbr_uri = self.doc.frbr_uri.work_uri()
            self.expression_date = self.doc.expression_date
            # ensure these are refreshed
            self._expression_uri = None

        # update the model's XML from the Act XML
        self.refresh_xml()

    def copy_attributes_from_work(self):
        """ Copy various attributes from this document's Work onto this
        document.
        """
        for attr in ['frbr_uri']:
            setattr(self, attr, getattr(self.work, attr))

        # copy over amendments at or before this expression date
        self.doc.amendments = self.amendment_events()

        # copy over title if it's not set
        if not self.title:
            self.title = self.work.title

    def update_search_text(self):
        """ Update the `search_text` field with a raw representation of all the text in the document.
        This is used by the `search_vector` field when doing full text search. The `search_vector`
        field is updated from the `search_text` field using a PostgreSQL trigger, installed by
        migration 0032.
        """
        xpath = '|'.join('//a:%s//text()' % c for c in ['coverPage', 'preface', 'preamble', 'body', 'mainBody', 'conclusions'])
        texts = self.doc.root.xpath(xpath, namespaces={'a': self.doc.namespace})
        self.search_text = ' '.join(texts)

    def refresh_xml(self):
        log.debug("Refreshing document xml for %s" % self)
        self.document_xml = self.doc.to_xml()

    def reset_xml(self, xml, from_model=False):
        """ Completely reset the document XML to a new value. If from_model is False,
        also refresh database attributes from the new XML document. """
        # this validates it
        doc = self._make_act(xml)

        # now update ourselves
        self._doc = doc
        self.copy_attributes(from_model)

    def table_of_contents(self):
        builder = plugins.for_document('toc', self)
        return builder.table_of_contents_for_document(self)

    def get_subcomponent(self, component, subcomponent):
        """ Get the named subcomponent in this document, such as `chapter/2` or 'section/13A'.
        :class:`lxml.objectify.ObjectifiedElement` or `None`.
        """
        def search_toc(items):
            for item in items:
                if item.component == component and item.subcomponent == subcomponent:
                    return item.element

                if item.children:
                    found = search_toc(item.children)
                    if found:
                        return found

        return search_toc(self.table_of_contents())

    def versions(self):
        """ Return a queryset of `reversion.models.Version` objects for
        revisions for this work, most recent first.
        """
        content_type = ContentType.objects.get_for_model(self)
        return reversion.models.Version.objects\
            .prefetch_related('revision')\
            .filter(content_type=content_type)\
            .filter(object_id_int=self.id)\
            .order_by('-id')

    def to_html(self, **kwargs):
        from .renderers import HTMLRenderer
        return HTMLRenderer().render(self, **kwargs)

    def element_to_html(self, element):
        """ Render a child element of this document into HTML. """
        from .renderers import HTMLRenderer
        return HTMLRenderer().render(self, element=element)

    def to_pdf(self, **kwargs):
        from .renderers import PDFRenderer
        return PDFRenderer().render(self, **kwargs)

    def element_to_pdf(self, element):
        """ Render a child element of this document into PDF. """
        from .renderers import PDFRenderer
        return PDFRenderer().render(self, element=element)

    def manifestation_url(self, fqdn=''):
        """ Fully-qualified manifestation URL.
        """
        if self.draft:
            return fqdn + reverse('document-detail', kwargs={'pk': self.id})
        else:
            return fqdn + '/api' + self.doc.expression_frbr_uri().manifestation_uri()

    def _make_act(self, xml):
        id = re.sub(r'[^a-zA-Z0-9]', '-', settings.INDIGO_ORGANISATION)
        doc = Act(xml)
        doc.source = [settings.INDIGO_ORGANISATION, id, settings.INDIGO_URL]
        return doc

    @property
    def django_language(self):
        return self.language.language.iso_639_1

    def __unicode__(self):
        return 'Document<%s, %s>' % (self.id, self.title[0:50])

    @classmethod
    def randomized(cls, frbr_uri, **kwargs):
        """ Helper to return a new document with a random FRBR URI
        """
        frbr_uri = FrbrUri.parse(frbr_uri)
        kwargs['work'] = Work.objects.get_for_frbr_uri(frbr_uri.work_uri())
        kwargs['language'] = Country.for_frbr_uri(frbr_uri).primary_language

        doc = cls(frbr_uri=frbr_uri.work_uri(False), expression_date=frbr_uri.expression_date, **kwargs)
        doc.copy_attributes()

        return doc


# version tracking
reversion.revisions.register(Document)
reversion.revisions.register(Work)


def attachment_filename(instance, filename):
    """ Make S3 attachment filenames relative to the document,
    this may be modified to ensure it's unique by the storage system. """
    return 'attachments/%s/%s' % (instance.document.id, os.path.basename(filename))


class Attachment(models.Model):
    document = models.ForeignKey(Document, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to=attachment_filename)
    size = models.IntegerField()
    filename = models.CharField(max_length=255, help_text="Unique attachment filename", db_index=True)
    mime_type = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TODO: enforce unique filename for document


@receiver(signals.pre_delete, sender=Attachment)
def delete_attachment(sender, instance, **kwargs):
    instance.file.delete()


class Subtype(models.Model):
    name = models.CharField(max_length=1024, help_text="Name of the document subtype")
    abbreviation = models.CharField(max_length=20, help_text="Short abbreviation to use in FRBR URI. No punctuation.", unique=True)

    class Meta:
        verbose_name = 'Document subtype'

    def clean(self):
        if self.abbreviation:
            self.abbreviation = self.abbreviation.lower()

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.abbreviation)


class Colophon(models.Model):
    """ A colophon is the chunk of text included at the
    start of the PDF and standalone HTML files. It includes
    copyright and attribution information and details on
    contacting the publisher.

    To determine which colophon to use for a document,
    Indigo choose the one which most closely matches
    the country of the document.
    """
    name = models.CharField(max_length=1024, help_text='Name of this colophon')
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=False, help_text='Which country does this colophon apply to?')
    body = models.TextField()

    def __unicode__(self):
        return unicode(self.name)


class Annotation(models.Model):
    document = models.ForeignKey(Document, related_name='annotations', on_delete=models.CASCADE)
    created_by_user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name='+')
    in_reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True)
    text = models.TextField(null=False, blank=False)
    anchor_id = models.CharField(max_length=512, null=False, blank=False)
    closed = models.BooleanField(default=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def anchor(self):
        return {'id': self.anchor_id}


class DocumentActivity(models.Model):
    """ Tracks user activity in a document, to help multiple editors see who's doing what.

    Clients ping the server every 5 seconds with a nonce that uniquely identifies them.
    If an entry with that nonce doesn't exist, it's created. Otherwise it's refreshed.
    Entries are vacuumed every ping, cleaning out stale entries.
    """
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=False, related_name='activities', db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name='document_activities')
    nonce = models.CharField(max_length=10, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # dead after we haven't heard from them in how long?
    DEAD_SECS = 2 * 60
    # asleep after we haven't heard from them in how long?
    ASLEEP_SECS = 1 * 60

    class Meta:
        unique_together = ('document', 'user', 'nonce')

    def touch(self):
        self.updated_at = timezone.now()

    def is_asleep(self):
        return (timezone.now() - self.updated_at).total_seconds() > self.ASLEEP_SECS

    @classmethod
    def vacuum(cls, document):
        threshold = timezone.now() - datetime.timedelta(seconds=cls.DEAD_SECS)
        cls.objects.filter(document=document, updated_at__lte=threshold).delete()
