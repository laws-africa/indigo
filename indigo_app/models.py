from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from rest_framework.authtoken.models import Token

from indigo_api.models import Country


class Editor(models.Model):
    """ A complement to Django's User model that adds extra
    properties that we need, like a default country.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    country = models.ForeignKey('indigo_api.Country', on_delete=models.SET_NULL, null=True)
    accepted_terms = models.BooleanField(default=False)
    permitted_countries = models.ManyToManyField(Country, related_name='editors', help_text="Countries the user can work with.", blank=True)

    @property
    def country_code(self):
        if self.country:
            return self.country.country_id.lower()
        return None

    @country_code.setter
    def country_code(self, value):
        if value is None:
            self.country = value
        else:
            self.country = Country.objects.get(country_id=value.upper())

    def has_country_permission(self, country):
        return self.user.is_superuser or country in self.permitted_countries.all()

    def api_token(self):
        # TODO: handle many
        return Token.objects.get_or_create(user=self.user)[0]


class Publication(models.Model):
    """ The publications available in the UI. They aren't enforced by the API.
    """
    country = models.ForeignKey('indigo_api.Country', null=False, on_delete=models.CASCADE)
    name = models.CharField(max_length=512, null=False, blank=False, unique=False, help_text="Name of this publication")

    class Meta:
        ordering = ['name']
        unique_together = (('country', 'name'),)

    def __unicode__(self):
        return unicode(self.name)


@receiver(post_save, sender=User)
def create_editor(sender, **kwargs):
    # create editor for user objects
    user = kwargs["instance"]
    if not hasattr(user, 'editor') and not kwargs.get('raw'):
        editor = Editor(user=user)
        # ensure there is a country
        editor.country = Country.objects.first()
        editor.save()
