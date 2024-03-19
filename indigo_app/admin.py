from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from .models import Editor, Publication
from indigo_api.models import Language, Country, Locality
from indigo_app.forms import CountryAdminForm


class EditorInline(admin.StackedInline):
    model = Editor
    can_delete = False
    verbose_name = 'Editor details'
    verbose_name_plural = 'editor'
    filter_horizontal = ('permitted_countries',)


class LocalityInline(admin.TabularInline):
    model = Locality
    can_delete = True
    extra = 0


class PublicationInline(admin.TabularInline):
    model = Publication
    can_delete = True
    extra = 0


# Define a new User admin
UserAdmin.inlines = UserAdmin.inlines + [EditorInline]


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    form = CountryAdminForm
    list_display = ('country',)
    inlines = (LocalityInline, PublicationInline)


admin.site.register(Language)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
