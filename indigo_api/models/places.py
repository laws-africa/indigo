from functools import lru_cache

from django.core.cache import cache
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
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

    class Meta:
        ordering = ['language__name_en']
        # also use the manager for related object lookups
        base_manager_name = 'objects'
        verbose_name = _("language")
        verbose_name_plural = _("languages")

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


class CountryManager(models.Manager):
    def get_queryset(self):
        # always load the related language model
        return super().get_queryset().select_related('country')


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

    objects = CountryManager()

    # Country.for_code and Country.get_country_locality are the main way to look up places. They are called many
    # times in the same request, but rarely change. So we cache them in-memory. Because we have multiple processes
    # we use the shared filesystem cache to store a version number that is incremented whenever a Country or Locality
    # is saved. This means that all processes will reload their in-memory cache the next time a country is requested.
    # This is the cache key
    CACHE_VERSION_KEY = "indigo-countries:v"

    class Meta:
        ordering = ['country__name']
        verbose_name = _("country")
        verbose_name_plural = _("countries")


    @property
    def code(self) -> str:
        """ISO 3166-1 alpha-2 country code."""
        return self.country.iso.lower()

    @property
    def name(self) -> str:
        """Name of the country in English."""
        return self.country.name

    @property
    def place_code(self):
        return self.code

    def place_tasks(self):
        return self.tasks.filter(locality=None)

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
        version = cache.get(cls.CACHE_VERSION_KEY, 0)
        countries = cls._load_all_countries(version)
        return countries.get(code)

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

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_all_countries(version: int):
        """ Loads all Country objects once per version. Returns a dict {code: Country instance}.
        The version parameter is just used to differentiate the LRU cache entries.
        """
        qs = Country.objects.all().prefetch_related('localities')
        return {c.code.lower(): c for c in qs}

    @classmethod
    def invalidate_country_cache(cls):
        """Increment the shared version in the global cache."""
        def _incr():
            try:
                cache.incr(cls.CACHE_VERSION_KEY)
            except ValueError:
                cache.add(cls.CACHE_VERSION_KEY, 1)
        # avoid race conditions and do it at the end of the transaction
        transaction.on_commit(_incr)


class AllPlace:
    """A fake country that mimics a country but is used to represent all places in the system."""
    place_code = code = iso = 'all'
    name = _('All places')

    @property
    def country(self):
        return self

    @classmethod
    def filter_works_queryset(cls, works, user):
        if not user.is_superuser:
            works = works.filter(country__in=user.editor.permitted_countries.all())
        return works


@receiver(signals.post_save, sender=Country)
def post_save_country(sender, instance, **kwargs):
    """ When a country is saved, make sure a PlaceSettings exists for it.
    """
    if not instance.settings:
        PlaceSettings.objects.create(country=instance)


class LocalityManager(models.Manager):
    def get_queryset(self):
        # always load the related language model
        return super().get_queryset().select_related('country', 'country__country')


class Locality(models.Model):
    """ The localities available in the UI. They aren't enforced by the API.
    """
    country = models.ForeignKey(Country, null=False, on_delete=models.CASCADE, related_name='localities',
                                verbose_name=_("country"))
    name = models.CharField(_("name"), max_length=512, null=False, blank=False, help_text=_("Local name of this locality"))
    code = models.CharField(_("code"), max_length=100, null=False, blank=False, help_text="Unique code of this locality (used in the FRBR URI)")

    objects = LocalityManager()

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

        return props


@receiver([signals.post_save, signals.post_delete], sender=Country)
@receiver([signals.post_save, signals.post_delete], sender=Locality)
@receiver([signals.post_save, signals.post_delete], sender=PlaceSettings)
def invalidate_country_cache(sender, instance, **kwargs):
    Country.invalidate_country_cache()


class AccentedTerms(models.Model):
    """ Accented terms for a language.
    """
    language = models.ForeignKey(Language, related_name='accented_terms', null=False, blank=False, unique=True,
                                 on_delete=models.CASCADE, verbose_name=_("language"))
    terms = ArrayField(models.CharField(_("terms"), max_length=1024), null=True, blank=True)

    class Meta:
        verbose_name = _("accented terms")
        verbose_name_plural = _("accented terms")

    def __str__(self):
        return str(self.language)


class CommonAnnotation(models.Model):
    title = models.CharField(_("annotation title"), max_length=32, help_text=_("to be shown in the document's drop-down menu"))
    content = models.CharField(_("annotation content"), max_length=512, help_text=_("will always be wrapped in []s — don't include them again"))
    language = models.ForeignKey(Language, verbose_name=_("language"), related_name='common_annotations', null=False, blank=False, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.title)
