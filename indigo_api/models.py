import logging

from django.db import models
import arrow

from cobalt.act import Act

COUNTRIES = sorted([
    ('za', 'South Africa'),
    ('zm', 'Zambia'),
    ])

# 3-letter ISO-639-2 language codes, see http://en.wikipedia.org/wiki/List_of_ISO_639-2_codes
LANGUAGES = sorted([
    ('eng', 'English'),
    ('fre', 'French'),
    ('swa', 'Swahili'),
    ('afr', 'Afrikaans'),
    ('por', 'Portuguese'),
    ])
DEFAULT_LANGUAGE = 'eng'

log = logging.getLogger(__name__)

class Document(models.Model):
    db_table = 'documents'

    frbr_uri = models.CharField(max_length=512, null=False, blank=False, default='/', help_text="Used globably to identify this work")
    """ The FRBR Work URI of this document that uniquely identifies it globally """

    title = models.CharField(max_length=1024, null=True, default='(untitled)')
    country = models.CharField(max_length=2, choices=COUNTRIES, default=COUNTRIES[0][0])

    """ The 3-letter ISO-639-2 language code of this document """
    language = models.CharField(max_length=3, choices=LANGUAGES, default=DEFAULT_LANGUAGE)
    draft = models.BooleanField(default=True, help_text="Drafts aren't available through the public API")
    """ Is this a draft? """

    document_xml = models.TextField(null=True, blank=True)
    """ Raw XML content of the entire document """

    publication_name = models.CharField(null=True, max_length=1024, help_text='Name of the original publication, such as a national gazette')
    publication_number = models.CharField(null=True, max_length=1024, help_text="Publication's sequence number, such as a gazette number")
    publication_date = models.DateField(null=True, blank=True)

    deleted = models.BooleanField(default=False, help_text="Has this document been deleted?")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

            self.doc.work_date = self.publication_date
            self.doc.manifestation_date = self.updated_at or arrow.now()

            self.doc.publication_date = self.publication_date or ''
            self.doc.publication_name = self.publication_name or ''
            self.doc.publication_number = self.publication_number or ''

        else:
            self.title = self.doc.title
            self.language = self.doc.language
            self.frbr_uri = self.doc.frbr_uri.work_uri()

            self.publication_date = self.doc.publication_date or self.doc.work_date
            self.publication_name = self.doc.publication_name
            self.publication_number = self.doc.publication_number

        # update the model's XML from the Act XML
        self.refresh_xml()

    def refresh_xml(self):
        log.debug("Refreshing document xml for %s" % self)
        self.document_xml = self.doc.to_xml()

    def reset_xml(self, xml):
        """ Completely reset the document XML to a new value, and refresh database attributes
        from the new XML document. """
        log.debug("Setting for %s xml to: %s" % (self, xml))

        # this validates it
        doc = Act(xml)

        # now update ourselves
        self._doc = doc
        self.copy_attributes(from_model=False)

    def table_of_contents(self):
        return [t.as_dict() for t in self.doc.table_of_contents()]

    def __unicode__(self):
        return 'Document<%s, %s>' % (self.id, (self.title or '(Untitled)')[0:50])
