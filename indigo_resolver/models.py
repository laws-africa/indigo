# coding=utf-8
import re

from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _


# our own slug validator that allows dots
slug_re = re.compile(r'^[-a-zA-Z0-9_.]+\Z')
validate_slug = RegexValidator(
    slug_re,
    _("Enter a valid 'slug' consisting of letters, numbers, underscores, dots or hyphens."),
    'invalid'
)


class Authority(models.Model):
    """ Authority that knows how to resolve
    FRBR URIs into real-world URLs.
    """
    name = models.CharField(max_length=255, unique=True, help_text="Descriptive name of this resolver")
    url = models.URLField(help_text="Website for this authority (optional)", blank=True, null=True)
    not_found_url = models.URLField(help_text="URL of a 404 page (optional)", null=True, blank=True)
    slug = models.CharField(null=False, blank=False, validators=[validate_slug], max_length=50, unique=True)
    priority = models.IntegerField(null=False, default=10, help_text="When multiple resolvers match, highest priority wins")

    class Meta:
        verbose_name_plural = "Authorities"

    def get_references(self, frbr_uri):
        # TODO: handle expression URIs and dates?
        refs = self.references\
            .filter(frbr_uri__in=[frbr_uri.work_uri(), frbr_uri.expression_uri()])\
            .prefetch_related('authority')\
            .all()
        # default priorities
        for r in refs:
            if r.priority is None:
                r.priority = self.priority
        return refs

    @property
    def reference_count(self):
        return self.references.count

    def __str__(self):
        return f'Authority<{self.name}>'


class AuthorityReference(models.Model):
    """ Reference to a particular document,
    belonging to a resolver.
    """
    frbr_uri = models.CharField(max_length=255, db_index=True, help_text="FRBR Work or Expression URI to match on")
    title = models.CharField(max_length=255, help_text="Document title")
    url = models.URLField(max_length=1024, help_text="URL from which this document can be retrieved")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    priority = models.IntegerField(null=True, blank=True, help_text="Priority for this URL. If unset, uses the authority's priority")

    authority = models.ForeignKey(Authority, related_name='references', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('authority', 'frbr_uri')

    def authority_name(self):
        if self.authority.url:
            return self.authority.name

        domain = self.url.split("/")[2].lower()
        if domain.startswith('www.'):
            domain = domain[4:]

        return domain

    def __str__(self):
        return f'{self.frbr_uri} – {self.title}'
