import json

from django import forms
from django.contrib import admin
from django.shortcuts import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from ckeditor.widgets import CKEditorWidget
from treebeard.admin import TreeAdmin
from treebeard.forms import MoveNodeForm, movenodeform_factory
from background_task.admin import TaskAdmin

from .models import Document, Subtype, Colophon, Work, TaskLabel, TaxonomyTopic, CitationAlias, SavedSearch


admin.site.register(Subtype)
admin.site.register(SavedSearch)


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
    # prevent pagination
    list_per_page = 1_000_000

    def changelist_view(self, request, extra_context=None):
        resp = super().changelist_view(request, extra_context)

        def fixup(item):
            item["title"] = item["data"]["name"]
            item["href"] = reverse("admin:indigo_api_taxonomytopic_change", args=[item["id"]])
            for kid in item.get("children", []):
                fixup(kid)

        # grab the tree and turn it into something la-table-of-contents-controller understands
        tree = self.model.dump_bulk()
        for x in tree:
            fixup(x)
        resp.context_data["tree_json"] = json.dumps(tree)

        return resp


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


@admin.register(CitationAlias)
class CitationAliasAdmin(admin.ModelAdmin):
    list_display = ('frbr_uri', 'place', 'aliases',)
    list_filter = ('place',)


def run_now(modeladmin, request, queryset):
    queryset.update(run_at=now())
    messages.success(request, _("Updated run time to now for selected tasks."))


run_now.short_description = _("Set run time to now")
TaskAdmin.actions.append(run_now)
