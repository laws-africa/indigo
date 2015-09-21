from django.db import models
from django.contrib.auth.models import User
from languages_plus.models import Language as MasterLanguage
from countries_plus.models import Country as MasterCountry


class Language(models.Model):
    """ The languages available in the UI. They aren't enforced by the API.
    """
    language = models.OneToOneField(MasterLanguage)

    class Meta:
        ordering = ['language__name_en']

    def __unicode__(self):
        return unicode(self.language)


class Country(models.Model):
    """ The countries available in the UI. They aren't enforced by the API.
    """
    country = models.OneToOneField(MasterCountry)

    class Meta:
        ordering = ['country__name']
        verbose_name_plural = 'Countries'

    def __unicode__(self):
        return unicode(self.country.name)


class Editor(models.Model):
    """ A complement to Django's User model that adds extra
    properties that we need, like a default country.
    """
    user = models.OneToOneField(User)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
