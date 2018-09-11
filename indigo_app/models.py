from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from rest_framework.authtoken.models import Token

from indigo_api.models import Document, Country


class Locality(models.Model):
    """ The localities available in the UI. They aren't enforced by the API.
    """
    country = models.ForeignKey('indigo_api.Country', null=False, on_delete=models.CASCADE)
    name = models.CharField(max_length=512, null=False, blank=False, help_text="Local name of this locality")
    code = models.CharField(max_length=100, null=False, blank=False, help_text="Unique code of this locality (used in the FRBR URI)")

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Localities'
        unique_together = (('country', 'code'),)

    def __unicode__(self):
        return unicode(self.name)

    @classmethod
    def for_work(cls, work):
        if work.locality:
            return work.country.work_locality(work)


class Editor(models.Model):
    """ A complement to Django's User model that adds extra
    properties that we need, like a default country.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    country = models.ForeignKey('indigo_api.Country', on_delete=models.SET_NULL, null=True)
    accepted_terms = models.BooleanField(default=False)

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


@receiver(pre_save, sender=User)
def set_user_email(sender, **kwargs):
    # ensure the user's username and email match
    user = kwargs["instance"]
    if user.email:
        user.username = user.email
    else:
        user.email = user.username


@receiver(post_save, sender=User)
def create_editor(sender, **kwargs):
    # create editor for user objects
    user = kwargs["instance"]
    if not hasattr(user, 'editor') and not kwargs.get('raw'):
        editor = Editor(user=user)
        # ensure there is a country
        editor.country = Country.objects.first()
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
