from django.contrib import admin

from .models import Document, Subtype

# Register your models here.
admin.site.register(Subtype)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    exclude = ['document_xml']
