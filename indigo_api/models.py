import os
import logging
from itertools import groupby

from django.db import models
from django.db.models import signals
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
import arrow
from taggit.managers import TaggableManager
import reversion

from cobalt.act import Act

DEFAULT_LANGUAGE = 'eng'
DEFAULT_COUNTRY = 'za'

log = logging.getLogger(__name__)


class DocumentQuerySet(models.QuerySet):
    def undeleted(self):
        return self.filter(deleted=False)

    def published(self):
        return self.filter(draft=False)

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

    objects = DocumentQuerySet.as_manager()

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

    stub = models.BooleanField(default=False, help_text="This is a placeholder document without full content")
    """ Is this a stub without full content? """

    deleted = models.BooleanField(default=False, help_text="Has this document been deleted?")

    # freeform tags via django-taggit
    tags = TaggableManager()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    updated_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

    @property
    def doc(self):
        """ The wrapped `an.act.Act` that this document works with. """
        if not getattr(self, '_doc', None):
            self._doc = Act(self.document_xml)
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
        return self.doc.year

    @property
    def number(self):
        return self.doc.number

    @property
    def nature(self):
        return self.doc.nature

    @property
    def subtype(self):
        return self.doc.frbr_uri.subtype

    @property
    def locality(self):
        return self.doc.frbr_uri.locality

    @property
    def publication_name(self):
        return self.doc.publication_name

    @publication_name.setter
    def publication_name(self, value):
        self.doc.publication_name = value

    @property
    def publication_number(self):
        return self.doc.publication_number

    @publication_number.setter
    def publication_number(self, value):
        self.doc.publication_number = value

    @property
    def publication_date(self):
        return self.doc.publication_date

    @publication_date.setter
    def publication_date(self, value):
        self.doc.publication_date = value

    @property
    def amendments(self):
        # we cache these values so that we can decorate them
        # with extra info when serializing
        if not hasattr(self, '_amendments') or self._amendments is None:
            self._amendments = self.doc.amendments
        return self._amendments

    @amendments.setter
    def amendments(self, value):
        self._amendments = None
        self._amended_versions = None
        self.doc.amendments = value

    @property
    def repeal(self):
        if not hasattr(self, '_repeal') or self._repeal is None:
            self._repeal = self.doc.repeal
        return self._repeal

    @repeal.setter
    def repeal(self, value):
        self._repeal = None
        self.doc.repeal = value

    def save(self, *args, **kwargs):
        self.copy_attributes()
        return super(Document, self).save(*args, **kwargs)

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

        else:
            self.title = self.doc.title
            self.language = self.doc.language
            self.frbr_uri = self.doc.frbr_uri.work_uri()
            self.expression_date = self.doc.expression_date
            # ensure these are refreshed
            self._amendments = None
            self._amended_versions = None
            self._repeal = None

        # update the model's XML from the Act XML
        self.refresh_xml()

    def refresh_xml(self):
        log.debug("Refreshing document xml for %s" % self)
        self.document_xml = self.doc.to_xml()

    def reset_xml(self, xml):
        """ Completely reset the document XML to a new value, and refresh database attributes
        from the new XML document. """
        # this validates it
        doc = Act(xml)

        # now update ourselves
        self._doc = doc
        self.copy_attributes(from_model=False)

    def table_of_contents(self):
        return [t.as_dict() for t in self.doc.table_of_contents()]

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

    def __unicode__(self):
        return 'Document<%s, %s>' % (self.id, (self.title or '(Untitled)')[0:50])

    @classmethod
    def decorate_amendments(cls, documents):
        """ Decorate the items in each document's ``amendments``
        list with the document id of the amending document.
        """
        # uris that amended docs in the set
        uris = set(a.amending_uri for d in documents for a in d.amendments if a.amending_uri)
        amending_docs = Document.objects\
            .filter(deleted__exact=False)\
            .filter(frbr_uri__in=list(uris))\
            .defer('document_xml')\
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
        repealing_docs = Document.objects\
            .filter(deleted__exact=False)\
            .filter(frbr_uri__in=list(uris))\
            .defer('document_xml')\
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
        docs = Document.objects\
            .filter(deleted__exact=False)\
            .filter(frbr_uri__in=uris)\
            .defer('document_xml')\
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


# version tracking
reversion.register(Document)


def attachment_filename(instance, filename):
    """ Make S3 attachment filenames relative to the document,
    this may be modified to ensure it's unique by the storage system. """
    return 'attachments/%s/%s' % (instance.document.id, os.path.basename(filename))


class Attachment(models.Model):
    document = models.ForeignKey(Document, related_name='attachments')
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
