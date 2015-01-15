from django.db import models

COUNTRIES = sorted([
        ('za', 'South Africa'),
        ('zm', 'Zambia'),
        ])

# Create your models here.
class Document(models.Model):
    db_table = 'documents'

    uri = models.CharField(max_length=512, null=True, unique=True)
    """ The FRBRuri of this document that uniquely identifies it globally """

    title = models.CharField(max_length=1024, null=True)
    country = models.CharField(max_length=2, choices=COUNTRIES, default=COUNTRIES[0][0])
    draft = models.BooleanField(default=True, help_text="Drafts aren't available through the public API")
    """ Is this a draft? """

    document_xml = models.TextField(null=True, blank=True)
    """ Raw XML content of the entire document """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return 'Document<%s, %s>' % (self.id, (self.title or '(Untitled)')[0:50])
