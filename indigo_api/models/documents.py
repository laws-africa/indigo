# coding=utf-8
import os
import logging
import re
import datetime

from actstream import action
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
from allauth.account.utils import user_display
from iso8601 import parse_date
from taggit.managers import TaggableManager
import reversion.revisions
import reversion.models
from cobalt.act import Act, FrbrUri, AmendmentEvent, datestring

from indigo.plugins import plugins
from indigo.documents import ResolvedAnchor

log = logging.getLogger(__name__)


class DocumentManager(models.Manager):
    def get_queryset(self):
        # defer expensive or unnecessary fields
        return super(DocumentManager, self) \
            .get_queryset() \
            .prefetch_related('work') \
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
                query = query.filter(expression_date=parse_date(expr_date[1:]).date())

            elif expr_date[0] == ':':
                # latest document at or before this date
                query = query \
                    .filter(expression_date__lte=parse_date(expr_date[1:]).date()) \
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


class DocumentMixin(object):
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

    @property
    def django_language(self):
        return self.language.language.iso_639_1

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

    def table_of_contents(self):
        builder = plugins.for_document('toc', self)
        return builder.table_of_contents_for_document(self)

    def to_html(self, **kwargs):
        from indigo_api.exporters import HTMLExporter
        exporter = HTMLExporter()
        exporter.media_url = reverse('document-detail', kwargs={'pk': self.id}) + '/'
        return exporter.render(self, **kwargs)

    def element_to_html(self, element):
        """ Render a child element of this document into HTML. """
        from indigo_api.exporters import HTMLExporter
        exporter = HTMLExporter()
        exporter.media_url = reverse('document-detail', kwargs={'pk': self.id}) + '/'
        return exporter.render(self, element=element)

    def to_pdf(self, **kwargs):
        from indigo_api.exporters import PDFExporter
        return PDFExporter().render(self, **kwargs)

    def element_to_pdf(self, element):
        """ Render a child element of this document into PDF. """
        from indigo_api.exporters import PDFExporter
        return PDFExporter().render(self, element=element)


class Document(DocumentMixin, models.Model):
    class Meta:
        permissions = (
            ('publish_document', 'Can publish and edit non-draft documents'),
            ('view_published_document', 'Can view publish documents through the API'),
            ('view_document_xml', 'Can view the source XML of documents'),
        )

    objects = DocumentManager.from_queryset(DocumentQuerySet)()

    work = models.ForeignKey('indigo_api.Work', on_delete=models.CASCADE, db_index=True, null=False)
    """ The work this document is an expression of. Details from the work will be inherited by this document.
    This is not exposed externally. Instead, the document is automatically linked to the appropriate
    work using the FRBR URI.

    You cannot create a document that has an FRBR URI that doesn't match a work.
    """

    frbr_uri = models.CharField(max_length=512, null=False, blank=False, default='/', help_text="Used globally to identify this work")
    """ The FRBR Work URI of this document that uniquely identifies it globally """

    title = models.CharField(max_length=1024, null=False)

    """ The 3-letter ISO-639-2 language code of this document """
    language = models.ForeignKey('indigo_api.Language', null=False, on_delete=models.PROTECT, help_text="Language this document is in.")
    draft = models.BooleanField(default=True, help_text="Drafts aren't available through the public API")
    """ Is this a draft? """

    document_xml = models.TextField(null=True, blank=True)
    """ Raw XML content of the entire document """

    # Date from the FRBRExpression element. This is either the publication date or the date of the last
    # amendment. This is used to identify this particular version of this work, so is stored in the DB.
    expression_date = models.DateField(null=False, blank=False, help_text="Date of publication or latest amendment")

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
    def expression_frbr_uri(self):
        """ The FRBR Expression URI as a string.
        """
        return self.expression_uri.expression_uri(False)

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

    def save_with_revision(self, user, comment=None):
        """ Save this document and create a new revision at the same time.
        """
        with reversion.revisions.create_revision():
            reversion.revisions.set_user(user)
            if comment:
                reversion.revisions.set_comment(comment)
            self.updated_by_user = user
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
        self.document_xml = self.doc.to_xml().decode('utf-8')

    def reset_xml(self, xml, from_model=False):
        """ Completely reset the document XML to a new value. If from_model is False,
        also refresh database attributes from the new XML document. """
        # this validates it
        doc = self._make_act(xml)

        # now update ourselves
        self._doc = doc
        self.copy_attributes(from_model)

    def versions(self):
        """ Return a queryset of `reversion.models.Version` objects for
        revisions for this work, most recent first.
        """
        content_type = ContentType.objects.get_for_model(self)
        return reversion.models.Version.objects \
            .select_related('revision') \
            .filter(content_type=content_type) \
            .filter(object_id_int=self.id) \
            .order_by('-id')

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

    def __str__(self):
        return 'Document<%s, %s>' % (self.id, self.title[0:50])

    @classmethod
    def randomized(cls, frbr_uri, **kwargs):
        """ Helper to return a new document with a random FRBR URI
        """
        from .works import Work
        from .places import Country

        frbr_uri = FrbrUri.parse(frbr_uri)
        kwargs['work'] = Work.objects.get_for_frbr_uri(frbr_uri.work_uri())
        kwargs['language'] = Country.for_frbr_uri(frbr_uri).primary_language

        doc = cls(frbr_uri=frbr_uri.work_uri(False), expression_date=frbr_uri.expression_date, **kwargs)
        doc.copy_attributes()

        return doc


# version tracking
reversion.revisions.register(Document)


@receiver(signals.post_save, sender=Document)
def post_save_document(sender, instance, **kwargs):
    """ Send action to activity stream, as 'created' if a new document.
        Update documents that have been deleted but don't send action to activity stream.
    """
    if kwargs['created']:
        action.send(instance.created_by_user, verb='created', action_object=instance,
                    place_code=instance.work.place.place_code)
    elif not instance.deleted:
        action.send(instance.updated_by_user, verb='updated', action_object=instance,
                    place_code=instance.work.place.place_code)


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

    class Meta:
        ordering = ('filename',)

    # TODO: enforce unique filename for document


@receiver(signals.pre_delete, sender=Attachment)
def delete_attachment(sender, instance, **kwargs):
    instance.file.delete()


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
    country = models.ForeignKey('indigo_api.Country', on_delete=models.CASCADE, null=False, help_text='Which country does this colophon apply to?')
    body = models.TextField()

    def __str__(self):
        return str(self.name)


class Annotation(models.Model):
    document = models.ForeignKey(Document, related_name='annotations', on_delete=models.CASCADE)
    created_by_user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name='+')
    in_reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True)
    text = models.TextField(null=False, blank=False)
    anchor_id = models.CharField(max_length=512, null=False, blank=False)
    closed = models.BooleanField(default=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    task = models.OneToOneField('task', on_delete=models.SET_NULL, null=True, related_name='annotation')
    selectors = JSONField(null=True)

    def resolve_anchor(self):
        if self.anchor_id and self.document:
            return ResolvedAnchor(self.anchor_id, self.selectors, self.document)

    def create_task(self, user):
        """ Create a new task for this annotation.
        """
        from .tasks import Task

        if self.in_reply_to:
            raise Exception("Cannot create tasks for reply annotations.")

        if not self.task:
            task = Task()
            task.country = self.document.work.country
            task.locality = self.document.work.locality
            task.work = self.document.work
            task.document = self.document
            task.anchor_id = self.anchor_id
            task.created_by_user = user
            task.updated_by_user = user

            anchor = self.resolve_anchor()
            ref = anchor.toc_entry.title if anchor.toc_entry else self.anchor_id

            # TODO: strip markdown?
            task.title = '"%s": %s' % (ref, self.text)
            if len(task.title) > 255:
                task.title = task.title[:250] + "..."
            task.description = '%s commented on "%s":\n\n%s' % (user_display(self.created_by_user), ref, self.text)

            task.save()
            self.task = task
            self.save()
            self.task.refresh_from_db()

        return self.task


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
        ordering = ('created_at',)

    def is_asleep(self):
        return (timezone.now() - self.updated_at).total_seconds() > self.ASLEEP_SECS

    @classmethod
    def vacuum(cls, document):
        threshold = timezone.now() - datetime.timedelta(seconds=cls.DEAD_SECS)
        cls.objects.filter(document=document, updated_at__lte=threshold).delete()
