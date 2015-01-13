from django.db import models

# Create your models here.
class Document(models.Model):
    db_table = 'documents'

    uri         = models.CharField(max_length=512, null=True, unique=True)
    """ The FRBRuri of this document that uniquely identifies it globally """

    title       = models.CharField(max_length=1024, null=True)
    draft       = models.BooleanField(default=True)
    """ Is this a draft? """

    content_xml = models.TextField(null=True, blank=True)
    """ Raw XML content of the entire document """

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
