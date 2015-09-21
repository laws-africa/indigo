from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from .models import Language, Country, Editor

# Register your models here.
admin.site.register(Language)
admin.site.register(Country)


class EditorInline(admin.StackedInline):
    model = Editor
    can_delete = False
    verbose_name = 'Editor details'
    verbose_name_plural = 'editor'


# Define a new User admin
class UserAdmin(UserAdmin):
    inlines = (EditorInline, )


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
