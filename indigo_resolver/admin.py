from django.contrib import admin

from .models import AuthorityReference, Authority


class AuthorityReferenceInline(admin.TabularInline):
    model = AuthorityReference
    can_delete = True


@admin.register(Authority)
class AuthorityAdmin(admin.ModelAdmin):
    inlines = (AuthorityReferenceInline, )
