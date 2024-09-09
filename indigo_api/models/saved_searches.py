from django.db import models
from django.utils.translation import gettext_lazy as _


class SavedSearch(models.Model):
    SCOPES = {
        "tasks": _("Tasks"),
        "works": _("Works"),
    }

    name = models.CharField(_("name"), max_length=255)
    scope = models.CharField(_("scope"), choices=SCOPES.items())
    querystring = models.CharField(_("querystring"), max_length=2048)

    class Meta:
        verbose_name = _("saved search")
        verbose_name_plural = _("saved searches")
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if self.querystring.startswith("http"):
            # just keep the querystring bit
            if '?' in self.querystring:
                self.querystring = self.querystring.split("?", 1)[1]
            else:
                self.querystring = "?"
        if not self.querystring.startswith("?"):
            self.querystring = "?" + self.querystring

        super().save(*args, **kwargs)

    def __str__(self):
        return f"SavedSearch<{self.name}: {self.SCOPES[self.scope]} - {self.querystring}>"
