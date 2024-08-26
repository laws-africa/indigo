from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from cobalt import FrbrUri


def validate_frbr_uri(value):
    try:
        if not value:
            raise ValueError()
        return FrbrUri.parse(value.lower()).work_uri()
    except ValueError:
        raise ValidationError(_("Invalid FRBR URI") + f": {value}")


class CitationAlias(models.Model):
    """ An explicit alias for a work used by the citator."""
    place = models.CharField(_("place"), max_length=1024, help_text=_("Two letter country code, with optional locality code"))
    frbr_uri = models.CharField(_("FRBR URI"), max_length=1024, validators=[validate_frbr_uri])
    aliases = models.TextField(_("aliases"), help_text=_("Aliases, one per line"))

    class Meta:
        ordering = ('frbr_uri',)
        unique_together = ('place', 'frbr_uri')
        verbose_name = _('Citation alias')
        verbose_name_plural = _('Citation aliases')

    def clean(self):
        self.aliases = '\n'.join([a.strip() for a in self.aliases.splitlines() if a.strip()])

    def __str__(self):
        return f'<CitationAlias #{self.pk}: {self.place} - {self.frbr_uri}>'

    @classmethod
    def aliases_for_frbr_uri(cls, frbr_uri):
        aliases = cls.objects.filter(place__in=[frbr_uri.place, frbr_uri.country])
        return {
            alias: a.frbr_uri
            for a in aliases
            for alias in a.aliases.splitlines()
            if alias
        }
