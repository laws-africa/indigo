from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from .models import Language, Country, Locality, Editor


class EditorInline(admin.StackedInline):
    model = Editor
    can_delete = False
    verbose_name = 'Editor details'
    verbose_name_plural = 'editor'


class LocalityInline(admin.TabularInline):
    model = Locality
    can_delete = True
    extra = 0


# Define a new User admin
class UserAdmin(UserAdmin):
    inlines = (EditorInline, )


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('country',)
    inlines = (LocalityInline, )


@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'country')


admin.site.register(Language)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
