from django.contrib import admin

from .models import Document, Subtype, Colophon

# Register your models here.
admin.site.register(Subtype)
admin.site.register(Colophon)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    exclude = ['document_xml']
