from django import forms
from django.contrib import admin
from ckeditor.widgets import CKEditorWidget

from .models import Document, Subtype, Colophon

# Register your models here.
admin.site.register(Subtype)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    exclude = ['document_xml']


class ColophonAdminForm(forms.ModelForm):
    body = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = Colophon


@admin.register(Colophon)
class ColophonAdmin(admin.ModelAdmin):
    form = ColophonAdminForm
