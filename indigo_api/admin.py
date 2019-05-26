from django import forms
from django.contrib import admin
from ckeditor.widgets import CKEditorWidget

from .models import Document, Subtype, Colophon, Work, TaskLabel, TaxonomyVocabulary

admin.site.register(Subtype)


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'frbr_uri', 'country',)
    list_filter = ('country',)
    readonly_fields = ('created_by_user', 'updated_by_user')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    exclude = ['document_xml', 'search_text']
    list_display = ('__str__', 'frbr_uri', 'draft', 'deleted')
    list_filter = ('work__country', 'draft', 'deleted')
    readonly_fields = ('created_by_user', 'updated_by_user')


class ColophonAdminForm(forms.ModelForm):
    body = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = Colophon
        fields = ('name', 'country', 'body')


@admin.register(Colophon)
class ColophonAdmin(admin.ModelAdmin):
    form = ColophonAdminForm


@admin.register(TaskLabel)
class TaskLabelAdmin(admin.ModelAdmin):
    list_display = ('title', 'description',)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(TaxonomyVocabulary)
class TaxonomyVocabularyAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'title', 'authority',)
    prepopulated_fields = {"slug": ("authority", "name")}



