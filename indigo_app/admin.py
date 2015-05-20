from django.contrib import admin

from .models import Language, Subtype, Country

# Register your models here.
admin.site.register(Language)
admin.site.register(Subtype)
admin.site.register(Country)
