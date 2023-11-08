from django import forms
from django.contrib import admin
from ckeditor.widgets import CKEditorWidget
from treebeard.admin import TreeAdmin
from treebeard.forms import MoveNodeForm, movenodeform_factory
from indigo_api.forms import NewWorkFormMixin, WorkAdminForm
from django.utils.translation import gettext_lazy as _

from .models import (
    Amendment,
    ArbitraryExpressionDate,
    Document,
    Subtype,
    Colophon,
    Work,
    TaskLabel,
    TaxonomyVocabulary,
    VocabularyTopic,
    TaxonomyTopic,
    Commencement,
    Task
)

admin.site.register(Subtype)


class TaxonomyForm(MoveNodeForm):
    def save(self, commit=True):
        super().save(commit=commit)
        # save all children so that the slugs take into account the potentially updated parent
        for node in self.instance.get_descendants():
            node.save()
        return self.instance


@admin.register(TaxonomyTopic)
class TaxonomyTopicAdmin(TreeAdmin):
    form = movenodeform_factory(TaxonomyTopic, TaxonomyForm)
    readonly_fields = ('slug',)
    search_fields = ('name', )


class CommencedInline(admin.StackedInline):
    verbose_name = 'commenced work'
    verbose_name_plural = 'commenced works'
    model = Commencement
    fk_name = 'commenced_work'
    extra = 1
    exclude = ('created_by_user', 'updated_by_user')


class CommencingInline(admin.StackedInline):
    verbose_name = 'commencing work'
    verbose_name_plural = 'commencing works'
    model = Commencement
    fk_name = 'commencing_work'
    exclude = ('created_by_user', 'updated_by_user')
    extra = 1


class AmendedInline(admin.StackedInline):
    verbose_name = 'amended work'
    verbose_name_plural = 'amended works'
    model = Amendment
    fk_name = 'amending_work'
    exclude = ('created_by_user', 'updated_by_user')
    extra = 1


class AmendingInline(admin.StackedInline):
    verbose_name = 'amending work'
    verbose_name_plural = 'amending works'
    model = Amendment
    fk_name = 'amended_work'
    exclude = ('created_by_user', 'updated_by_user')
    extra = 1


class ConsolidationDateInline(admin.StackedInline):
    verbose_name = 'consolidation date'
    verbose_name_plural = 'consolidation dates'
    model = ArbitraryExpressionDate
    exclude = ('created_by_user', 'updated_by_user', 'description')
    extra = 1


class RepealsInline(admin.StackedInline):
    verbose_name = 'repealed work'
    verbose_name_plural = 'repealed works'
    fk_name = 'repealed_by'
    model = Work
    fields = ('frbr_uri',)
    extra = 1


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    form = WorkAdminForm
    autocomplete_fields = ('taxonomy_topics',)
    list_display = ('__str__', 'frbr_uri', 'country',)
    list_filter = ('country',)
    exclude = ('taxonomies', 'created_by_user', 'updated_by_user')
    inlines = (
        CommencingInline,
        CommencedInline,
        AmendingInline,
        AmendedInline,
        ConsolidationDateInline,
        RepealsInline,
    )

    new_document_form_mixin = NewWorkFormMixin

    def save_formset(self, request, form, formset, change):
        # add user to created_by_user and updated_by_user fields
        instances = formset.save(commit=False)
        for instance in instances:
            instance.created_by_user = request.user
            instance.updated_by_user = request.user
            instance.save()
        formset.save_m2m()

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs["fields"] = self.new_document_form_mixin.remove_fields(
                kwargs["fields"]
            )
            form = super().get_form(request, obj, **kwargs)

            class NewForm(self.new_document_form_mixin, form):
                pass
            return NewForm
        return super().get_form(request, obj, **kwargs)

    def get_fields(self, request, obj=None):
        if obj is None:
            return self.new_document_form_mixin.adjust_fields(
                super().get_fields(request, obj)
            )
        return super().get_fields(request, obj)

    def save_model(self, request, obj, form, change):

        if not change:
            obj.created_by_user = request.user
        obj.updated_by_user = request.user

        if form.cleaned_data.get('skip_signoff'):
            obj.properties["skip_signoff"] = True

        super().save_model(request, obj, form, change)
        self.create_tasks(obj, request.user, form.cleaned_data)

    def create_tasks(self, work, user, cleaned_data):
        if cleaned_data.get('principal'):
            self.create_import_task(work, user, cleaned_data)

    def create_import_task(self, work, user, cleaned_data):
        if Task.objects.filter(work=work, code='import-content').exists():
            return

        task_type = 'import-content'
        title = _('Import content')
        description = _(
            "Import the content for this work – either the initial publication (usually a PDF of the Gazette)" +
            " or a later consolidation (usually a .docx file)."
        )
        task_params = {
            'task_type': task_type,
            'title': title,
            'description': description,
            'work': work,
            'user': user,
        }
        task = self.create_task(**task_params)
        task.save()
        if cleaned_data.get('block_import_task'):
            task.block()
            task.save()

    def create_task(self, task_type, title, description, work, user):
        task = Task()
        task.title = title
        task.description = description
        task.country = work.country
        task.locality = work.locality
        task.work = work
        task.code = task_type
        task.created_by_user = user
        task.save()
        return task


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


class VocabularyTopicInline(admin.TabularInline):
    model = VocabularyTopic
    can_delete = True
    extra = 3
    fields = ('level_1', 'level_2', 'slug')
    readonly_fields = ('slug',)


@admin.register(TaxonomyVocabulary)
class TaxonomyVocabularyAdmin(admin.ModelAdmin):
    list_display = ('title', 'authority', '__str__')
    prepopulated_fields = {"slug": ("authority", "name")}
    inlines = (VocabularyTopicInline, )
    fields = ('title', 'authority', 'name', 'slug')
