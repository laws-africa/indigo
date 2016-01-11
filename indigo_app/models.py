from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from languages_plus.models import Language as MasterLanguage
from countries_plus.models import Country as MasterCountry

from indigo_api.models import Document


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

    @property
    def code(self):
        return self.country.iso.lower()

    @property
    def name(self):
        return self.country.name

    def as_json(self):
        return {
            'name': self.name,
            'localities': {loc.code: loc.name for loc in self.locality_set.all()},
        }

    def __unicode__(self):
        return unicode(self.country.name)


class Locality(models.Model):
    """ The localities available in the UI. They aren't enforced by the API.
    """
    country = models.ForeignKey(Country, null=False)
    name = models.CharField(max_length=512, null=False, blank=False, help_text="Local name of this locality")
    code = models.CharField(max_length=100, null=False, blank=False, help_text="Unique code of this locality (used in the FRBR URI)")

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Localities'
        unique_together = (('country', 'code'),)

    def __unicode__(self):
        return unicode(self.name)


class Editor(models.Model):
    """ A complement to Django's User model that adds extra
    properties that we need, like a default country.
    """
    user = models.OneToOneField(User)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)

    @property
    def country_code(self):
        if self.country:
            return self.country.country_id
        return None

    @country_code.setter
    def country_code(self, value):
        if value is None:
            self.country = value
        else:
            self.country = Country.objects.get(country_id=value.upper())


@receiver(post_save, sender=User)
def create_editor(sender, **kwargs):
    # create editor for user objects
    user = kwargs["instance"]
    if not hasattr(user, 'editor'):
        editor = Editor(user=user)
        editor.save()


@receiver(post_save, sender=Document)
def update_user_country(sender, **kwargs):
    # default country for user
    document = kwargs["instance"]
    user = document.updated_by_user

    if user and user.editor and not user.editor.country and document.country:
        try:
            user.editor.country_code = document.country
            user.editor.save()
        except Country.DoesNotExist:
            pass
