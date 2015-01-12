from django.db import models

# Create your models here.
class Document(models.Model):
    db_table = 'documents'

    uri = models.CharField(max_length=512)
