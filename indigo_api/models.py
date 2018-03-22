import os
import logging
from itertools import groupby
import re
import random
import datetime
import string

from django.conf import settings
from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.fields import JSONField
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
import arrow
from taggit.managers import TaggableManager
import reversion.revisions
import reversion.models

from countries_plus.models import Country as MasterCountry

from cobalt.act import Act, FrbrUri, RepealEvent, AmendmentEvent, datestring

from .utils import language3_to_2, localize_toc

DEFAULT_LANGUAGE = 'eng'
DEFAULT_COUNTRY = 'za'

log = logging.getLogger(__name__)


class WorkQuerySet(models.QuerySet):
    def undeleted(self):
        return self.filter(deleted=False)


class Work(models.Model):
    """ A work is an abstract document, such as an act. It has basic metadata and
    allows us to track works that we don't have documents for, and provides a
    logical parent for documents, which are expressions of a work.
    """

    frbr_uri = models.CharField(max_length=512, null=False, blank=False, default='/', help_text="Used globally to identify this work")
    """ The FRBR Work URI of this work that uniquely identifies it globally """

    title = models.CharField(max_length=1024, null=True, default='(untitled)')
    country = models.CharField(max_length=2, default=DEFAULT_COUNTRY)

    draft = models.BooleanField(default=True, help_text="Drafts aren't available through the public API")
    """ Is this a draft? """

    deleted = models.BooleanField(default=False, help_text="Has this work been deleted?")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    updated_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

    objects = WorkQuerySet.as_manager()

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


class DocumentManager(models.Manager):
    def get_queryset(self):
        # defer expensive or unnecessary fields
        return super(DocumentManager, self)\
            .get_queryset()\
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
        """
        query = self.filter(frbr_uri=frbr_uri.work_uri())

        # filter on expression date
        expr_date = frbr_uri.expression_date
        if expr_date:
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

        else:
            # always get the latest expression
            query = query.order_by('-expression_date')

        obj = query.first()
        if obj is None:
            raise ValueError("Document doesn't exist")

        if obj and frbr_uri.language and obj.language != frbr_uri.language:
            raise ValueError("The document %s exists but is not available in the language '%s'"
                             % (frbr_uri.work_uri(), frbr_uri.language))

        return obj


class Document(models.Model):
    class Meta:
        permissions = (
            ('publish_document', 'Can publish and edit non-draft documents'),
        )

    objects = DocumentManager.from_queryset(DocumentQuerySet)()

    db_table = 'documents'

    frbr_uri = models.CharField(max_length=512, null=False, blank=False, default='/', help_text="Used globally to identify this work")
    """ The FRBR Work URI of this document that uniquely identifies it globally """

    title = models.CharField(max_length=1024, null=True, default='(untitled)')
    country = models.CharField(max_length=2, default=DEFAULT_COUNTRY)

    """ The 3-letter ISO-639-2 language code of this document """
    language = models.CharField(max_length=3, default=DEFAULT_LANGUAGE)
    draft = models.BooleanField(default=True, help_text="Drafts aren't available through the public API")
    """ Is this a draft? """

    document_xml = models.TextField(null=True, blank=True)
    """ Raw XML content of the entire document """

    # Date from the FRBRExpression element. This is either the publication date or the date of the last
    # amendment. This is used to identify this particular version of this work, so is stored in the DB.
    # It can be null only so that users aren't forced to add a value.
    expression_date = models.DateField(null=True, blank=True, help_text="Date of publication or latest amendment")

    # Date of commencement. AKN doesn't have a good spot for this, so it only goes in the DB.
    commencement_date = models.DateField(null=True, blank=True, help_text="Date of commencement unless otherwise specified")
    # Date of assent. AKN doesn't have a good spot for this, so it only goes in the DB.
    assent_date = models.DateField(null=True, blank=True, help_text="Date signed by the president")

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

    # extra details which are primarily stored in the XML, but which are first class API attributes
    # so we cache them in the database
    publication_name = models.CharField(null=True, blank=True, max_length=255)
    publication_date = models.CharField(null=True, blank=True, max_length=255)
    publication_number = models.CharField(null=True, blank=True, max_length=255)
    repeal_event = JSONField(null=True)
    amendment_events = JSONField(null=True)

    # caching attributes
    _repeal = None
    _amendments = None
    _work_uri = None

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
        self.reset_xml(value)

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
    def amendments(self):
        # we cache these values so that we can decorate them
        # with extra info when serializing
        if self._amendments is None:
            self._amendments = [
                AmendmentEvent(
                    arrow.get(a.get('date')).date() if a.get('date') else None,
                    a.get('amending_title'),
                    a.get('amending_uri')
                ) for a in self.amendment_events or []]
        return self._amendments

    @amendments.setter
    def amendments(self, value):
        self._amendments = None
        self._amended_versions = None
        if value:
            self.amendment_events = [{
                'date': datestring(a.date) if a.date else None,
                'amending_title': a.amending_title,
                'amending_uri': a.amending_uri,
            } for a in value]
        else:
            self.amendment_events = None

    @property
    def repeal(self):
        if self._repeal is None:
            e = self.repeal_event
            if e:
                d = e.get('date')
                d = arrow.get(d).date() if d else None
                self._repeal = RepealEvent(d, e.get('repealing_title'), e.get('repealing_uri'))
        return self._repeal

    @repeal.setter
    def repeal(self, value):
        self._repeal = None
        if value:
            self.repeal_event = {
                'date': datestring(value.date),
                'repealing_title': value.repealing_title,
                'repealing_uri': value.repealing_uri,
            }
        else:
            self.repeal_event = None

    @property
    def work_uri(self):
        """ The FRBR Work URI as a :class:`FrbrUri` instance that uniquely identifies this document universally. """
        if self._work_uri is None:
            self._work_uri = FrbrUri.parse(self.frbr_uri)
        return self._work_uri

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
        """ Copy attributes from the model into the document, or reverse
        if `from_model` is False. """

        if from_model:
            self.doc.title = self.title
            self.doc.frbr_uri = self.frbr_uri
            self.doc.language = self.language

            self.doc.work_date = self.doc.publication_date
            self.doc.expression_date = self.expression_date or self.doc.publication_date or arrow.now()
            self.doc.manifestation_date = self.updated_at or arrow.now()
            self.doc.publication_number = self.publication_number
            self.doc.publication_name = self.publication_name
            self.doc.publication_date = self.publication_date
            self.doc.repeal = self.repeal
            self.doc.amendments = self.amendments

        else:
            self.title = self.doc.title
            self.language = self.doc.language
            self.frbr_uri = self.doc.frbr_uri.work_uri()
            self.expression_date = self.doc.expression_date
            self.publication_number = self.doc.publication_number
            self.publication_name = self.doc.publication_name
            self.publication_date = self.doc.publication_date
            self.repeal = self.doc.repeal
            self.amendments = self.doc.amendments
            # ensure these are refreshed
            self._work_uri = None
            self._amendments = None
            self._amended_versions = None
            self._repeal = None

        # update the model's XML from the Act XML
        self.refresh_xml()

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

    def reset_xml(self, xml):
        """ Completely reset the document XML to a new value, and refresh database attributes
        from the new XML document. """
        # this validates it
        doc = self._make_act(xml)

        # now update ourselves
        self._doc = doc
        self.copy_attributes(from_model=False)

    def table_of_contents(self):
        toc = self.doc.table_of_contents()
        localize_toc(toc, self.django_language)
        return [t.as_dict() for t in toc]

    def amended_versions(self):
        """ Return a list of all the amended versions of this work.
        This is all documents that share the same URI but have different
        expression dates.

        If there are no document besides this one, an empty list is returned.
        """
        if not hasattr(self, '_amended_versions'):
            Document.decorate_amended_versions([self])

        return self._amended_versions

    def revisions(self):
        """ Return a queryset of `reversion.models.Revision` objects for
        revisions for this document, most recent first.
        """
        content_type = ContentType.objects.get_for_model(self)
        return reversion.models.Revision.objects\
            .filter(version__content_type=content_type)\
            .filter(version__object_id_int=self.id)\
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
        return language3_to_2(self.language) or self.language

    def __unicode__(self):
        return 'Document<%s, %s>' % (self.id, (self.title or '(Untitled)')[0:50])

    @classmethod
    def decorate_amendments(cls, documents):
        """ Decorate the items in each document's ``amendments``
        list with the document id of the amending document.
        """
        # uris that amended docs in the set
        uris = set(a.amending_uri for d in documents for a in d.amendments if a.amending_uri)
        amending_docs = Document.objects.undeleted().no_xml()\
            .filter(frbr_uri__in=list(uris))\
            .order_by('expression_date')\
            .all()

        for doc in documents:
            for a in doc.amendments:
                for amending in amending_docs:
                    # match on the URI and the expression date
                    if amending.frbr_uri == a.amending_uri and amending.expression_date == a.date:
                        a.amending_document = amending
                        break

    @classmethod
    def decorate_repeal(cls, documents):
        """ Decorate the repeal item of each document (if set) with the
        document id of the repealing document.
        """
        # uris that amended docs in the set
        uris = set(d.repeal.repealing_uri for d in documents if d.repeal)
        repealing_docs = Document.objects.undeleted().no_xml()\
            .filter(frbr_uri__in=list(uris))\
            .order_by('expression_date')\
            .all()

        for doc in documents:
            if doc.repeal:
                repeal = doc.repeal

                for repealing in repealing_docs:
                    # match on the URI and the expression date
                    if repealing.frbr_uri == repeal.repealing_uri and repealing.expression_date == repeal.date:
                        repeal.repealing_document = repealing
                        break

    @classmethod
    def decorate_amended_versions(cls, documents):
        """ Decorate each documents with ``_amended_versions``, a (possibly empty)
        list of all the documents which form the same group of amended versions.
        """
        uris = [d.frbr_uri for d in documents]
        docs = Document.objects.undeleted().no_xml()\
            .filter(frbr_uri__in=uris)\
            .order_by('frbr_uri', 'expression_date')\
            .all()

        # group by URI
        groups = {}
        for uri, group in groupby(docs, lambda d: d.frbr_uri):
            groups[uri] = list(group)

        for doc in documents:
            amended_versions = groups.get(doc.frbr_uri, [])

            # there are no amended versions if this is the only one
            if len(amended_versions) == 0 or (len(amended_versions) == 1 and amended_versions[0].id == doc.id):
                doc._amended_versions = []
            else:
                doc._amended_versions = amended_versions

    @classmethod
    def randomized(cls, user=None, **kwargs):
        """ Helper to return a new document with a random FRBR URI
        """
        country = kwargs.pop('country', None) or (user.editor.country_code if user and user.is_authenticated else None)
        frbr_uri = random_frbr_uri(country=country)

        doc = cls(frbr_uri=frbr_uri.work_uri(False), publication_date=frbr_uri.expression_date, expression_date=frbr_uri.expression_date, **kwargs)
        doc.copy_attributes()

        return doc


# version tracking
reversion.revisions.register(Document)


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
    country = models.ForeignKey(MasterCountry, on_delete=models.SET_NULL, null=True, blank=True, help_text='Which country does this colophon apply to?')
    body = models.TextField()

    def __unicode__(self):
        return unicode(self.name)


def random_frbr_uri(country=None):
    today = datetime.datetime.now()
    number = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in xrange(5))
    country = country or DEFAULT_COUNTRY
    return FrbrUri(country=country.lower(), locality=None, doctype="act",
                   subtype=None, actor=None, date=str(today.year),
                   expression_date=today.strftime("%Y-%m-%d"),
                   number=number.lower())


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
