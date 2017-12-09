from __future__ import unicode_literals

from django.db import models


class Authority(models.Model):
    """ Authority that knows how to resolve
    FRBR URIs into real-world URLs.
    """
    name = models.CharField(max_length=255, unique=True, help_text="Descriptive name of this resolver")
    url = models.URLField(help_text="Website for this authority (optional)", blank=True, null=True)

    class Meta:
        verbose_name_plural = "Authorities"

    @property
    def reference_count(self):
        return self.references.count

    def __str__(self):
        return u'Authority<%s>' % self.name


class AuthorityReference(models.Model):
    """ Reference to a particular document,
    belonging to a resolver.
    """
    frbr_uri = models.CharField(max_length=255, db_index=True, help_text="FRBR Work or Expression URI to match on")
    title = models.CharField(max_length=255, help_text="Document title")
    url = models.URLField(max_length=1024, help_text="URL from which this document can be retrieved")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
        return u'%s - "%s"' % (self.frbr_uri, self.title)
