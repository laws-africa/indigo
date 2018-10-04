from django.contrib import admin

from .models import AuthorityReference, Authority


class AuthorityReferenceInline(admin.TabularInline):
    model = AuthorityReference
    can_delete = True
    ordering = ('frbr_uri',)


@admin.register(Authority)
class AuthorityAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'reference_count')
    inlines = (AuthorityReferenceInline, )
    prepopulated_fields = {"slug": ("name",)}
