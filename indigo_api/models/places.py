from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import signals
from django.dispatch import receiver

from countries_plus.models import Country as MasterCountry
from languages_plus.models import Language as MasterLanguage


class LanguageManager(models.Manager):
    def get_queryset(self):
        # always load the related language model
        return super().get_queryset().select_related('language')


class Language(models.Model):
    """ The languages available in the UI. They aren't enforced by the API.
    """
    language = models.OneToOneField(MasterLanguage, on_delete=models.CASCADE, verbose_name=_("language"))
    objects = LanguageManager()
    verbose_name = _("language")
    verbose_name_plural = _("languages")

    class Meta:
        ordering = ['language__name_en']
        # also use the manager for related object lookups
        base_manager_name = 'objects'

    @property
    def code(self):
        """ 3 letter language code.
        """
        return self.language.iso_639_2T

    def __str__(self):
        return str(self.language)

    @classmethod
    def for_code(cls, code):
        return cls.objects.get(language__iso_639_2T=code)


class Country(models.Model):
    """ The countries available in the UI. They aren't enforced by the API.
    """
    country = models.OneToOneField(MasterCountry, on_delete=models.CASCADE, verbose_name=_("country"))
    primary_language = models.ForeignKey(Language, on_delete=models.PROTECT, null=False, related_name='+',
                                         help_text=_("Primary language for this country"),
                                         verbose_name=_("primary language"))
    italics_terms = ArrayField(
        models.CharField(_("italics terms"), max_length=1024),
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['country__name']
        verbose_name = _("country")
        verbose_name_plural = _("countries")

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

    @cached_property
    def settings(self):
        """ PlaceSettings object for this country.
        """
        return self.place_settings.filter(locality=None).first()

    def as_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'localities': [loc.as_json() for loc in self.localities.all()],
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
    country = models.ForeignKey(Country, null=False, on_delete=models.CASCADE, related_name='localities',
                                verbose_name=_("country"))
    name = models.CharField(_("name"), max_length=512, null=False, blank=False, help_text=_("Local name of this locality"))
    code = models.CharField(_("code"), max_length=100, null=False, blank=False, help_text="Unique code of this locality (used in the FRBR URI)")

    class Meta:
        ordering = ['name']
        verbose_name = _("locality")
        verbose_name_plural = _('localities')
        unique_together = (('country', 'code'),)

    @property
    def place_code(self):
        return self.country.code + '-' + self.code

    def place_tasks(self):
        return self.tasks

    def place_workflows(self):
        return self.workflows

    def as_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
        }

    @cached_property
    def settings(self):
        """ PlaceSettings object for this place.
        """
        return self.place_settings.first()

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
    country = models.ForeignKey(Country, related_name='place_settings', null=False, blank=False,
                                on_delete=models.CASCADE, verbose_name=_("country"))
    locality = models.ForeignKey(Locality, related_name='place_settings', null=True, blank=True,
                                 on_delete=models.CASCADE, verbose_name=_("locality"))

    spreadsheet_url = models.URLField(_("spreadsheet URL"), null=True, blank=True)
    as_at_date = models.DateField(_("as-at date"), null=True, blank=True)
    styleguide_url = models.URLField(_("styleguide URL"), null=True, blank=True)
    consolidation_note = models.CharField(_("consolidation note"), max_length=1024, null=True, blank=True)
    no_publication_document_text = models.CharField(
        _("'No publication document' text"), max_length=1024, null=False, blank=True,
        default=_("Note: The original publication document is not available and this content could not be verified."))
    publication_date_optional = models.BooleanField(_("publication date is optional"), default=False, null=False,
                                                    help_text=_("Are publication dates optional in this place?"))
    is_consolidation = models.BooleanField(_("a consolidation is being imported"), default=False, null=False,
                                           help_text=_("Is a consolidation being worked on in this place?"))
    uses_chapter = models.BooleanField(_("chapters are used"), default=False, null=False,
                                       help_text=_("Are Chapters used for Acts in this place?"))

    class Meta:
        verbose_name = _("place settings")
        verbose_name_plural = _("places' settings")

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
        props = None

        # get base properties from settings
        if self.locality:
            props = places.get(self.locality.place_code)
        if props is None:
            props = places.get(self.country.place_code, {})

        # optionally add / overwrite cap
        if self.uses_chapter:
            props['cap'] = _("Chapter (Cap.)")

        return props
