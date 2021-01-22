# coding=utf-8
from django.utils.translation import ugettext_lazy as _

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from countries_plus.models import Country as MasterCountry
from languages_plus.models import Language as MasterLanguage


class Language(models.Model):
    """ The languages available in the UI. They aren't enforced by the API.
    """
    language = models.OneToOneField(MasterLanguage, on_delete=models.CASCADE)

    class Meta:
        ordering = ['language__name_en']

    @property
    def code(self):
        """ 3 letter language code.
        """
        return self.language.iso_639_2B

    def __str__(self):
        return str(self.language)

    @classmethod
    def for_code(cls, code):
        return cls.objects.get(language__iso_639_2B=code)


class Country(models.Model):
    """ The countries available in the UI. They aren't enforced by the API.
    """
    country = models.OneToOneField(MasterCountry, on_delete=models.CASCADE)
    primary_language = models.ForeignKey(Language, on_delete=models.PROTECT, null=False, related_name='+', help_text='Primary language for this country')
    italics_terms = ArrayField(
        models.CharField(max_length=1024),
        null=True,
        blank=True
    )

    _settings = None

    class Meta:
        ordering = ['country__name']
        verbose_name_plural = 'Countries'

    @property
    def code(self):
        return self.country.iso.lower()

    @property
    def name(self):
        return self.country.name

    @property
    def place_code(self):
        return self.code

    def place_tasks(self):
        return self.tasks.filter(locality=None)

    def place_workflows(self):
        return self.workflows.filter(locality=None)

    @property
    def settings(self):
        """ PlaceSettings object for this country.
        """
        if not self._settings:
            self._settings = self.place_settings.filter(locality=None).first()
        return self._settings

    def as_json(self):
        return {
            'name': self.name,
            'localities': {loc.code: loc.name for loc in self.localities.all()},
            'publications': [pub.name for pub in self.publication_set.all()],
        }

    def __str__(self):
        return str(self.country.name)

    @classmethod
    def for_frbr_uri(cls, frbr_uri):
        return cls.for_code(frbr_uri.country)

    @classmethod
    def for_code(cls, code):
        return cls.objects.get(country__pk=code.upper())

    @classmethod
    def get_country_locality(cls, code):
        """ Lookup a Country and Locality for a place code such as za or za-cpt.

        Raises DoesNotExist if either of the places doesn't exist.
        """
        if '-' in code:
            country_code, locality_code = code.split('-', 1)
        else:
            country_code = code
            locality_code = None

        country = cls.for_code(country_code)
        if locality_code:
            locality = country.localities.get(code=locality_code)
        else:
            locality = None

        return country, locality


@receiver(signals.post_save, sender=Country)
def post_save_country(sender, instance, **kwargs):
    """ When a country is saved, make sure a PlaceSettings exists for it.
    """
    if not instance.settings:
        PlaceSettings.objects.create(country=instance)


class Locality(models.Model):
    """ The localities available in the UI. They aren't enforced by the API.
    """
    country = models.ForeignKey(Country, null=False, on_delete=models.CASCADE, related_name='localities')
    name = models.CharField(max_length=512, null=False, blank=False, help_text="Local name of this locality")
    code = models.CharField(max_length=100, null=False, blank=False, help_text="Unique code of this locality (used in the FRBR URI)")

    _settings = None

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Localities'
        unique_together = (('country', 'code'),)

    @property
    def place_code(self):
        return self.country.code + '-' + self.code

    def place_tasks(self):
        return self.tasks

    def place_workflows(self):
        return self.workflows

    @property
    def settings(self):
        """ PlaceSettings object for this place.
        """
        if not self._settings:
            self._settings = self.place_settings.first()
        return self._settings

    def __str__(self):
        return str(self.name)


@receiver(signals.post_save, sender=Locality)
def post_save_locality(sender, instance, **kwargs):
    """ When a locality is saved, make sure a PlaceSettings exists for it.
    """
    if not instance.settings:
        PlaceSettings.objects.create(country=instance.country, locality=instance)


class PlaceSettings(models.Model):
    """ General settings for a country (and/or locality).
    """
    country = models.ForeignKey(Country, related_name='place_settings', null=False, blank=False, on_delete=models.CASCADE)
    locality = models.ForeignKey(Locality, related_name='place_settings', null=True, blank=True, on_delete=models.CASCADE)

    spreadsheet_url = models.URLField(null=True, blank=True)
    as_at_date = models.DateField(null=True, blank=True)
    styleguide_url = models.URLField(null=True, blank=True)
    no_publication_document_text = models.CharField(
        max_length=1024, null=False, blank=True,
        default=_('Note: The original publication document is not available and this content could not be verified.'))

    @property
    def place(self):
        return self.locality or self.country

    @property
    def work_properties(self):
        """ Return a dict of place-specific properties for works.

        For a locality, looks for locality-specific settings before falling back to
        country settings.
        """
        places = settings.INDIGO['WORK_PROPERTIES']

        if self.locality:
            props = places.get(self.locality.place_code)
            if props is not None:
                return props

        return places.get(self.country.place_code, {})
