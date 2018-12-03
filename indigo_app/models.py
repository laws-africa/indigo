from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from rest_framework.authtoken.models import Token

from indigo_api.models import Country, Locality, Work, Document


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


class Task(models.Model):
    title = models.CharField(max_length=256, null=False, blank=False)
    content = models.TextField(null=True, blank=True)

    country = models.ForeignKey(Country, related_name='tasks', null=False, blank=False, on_delete=models.CASCADE)
    locality = models.ForeignKey(Locality, related_name='tasks', null=True, blank=True, on_delete=models.CASCADE)
    work = models.ForeignKey(Work, related_name='tasks', null=True, blank=True, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, related_name='tasks', null=True, blank=True, on_delete=models.CASCADE)

    # cf indigo_api.models.Annotation
    anchor_id = models.CharField(max_length=128, null=True, blank=True)

    state = models.CharField(max_length=128, null=False, blank=False, choices=(
        ('open', 'open'), ('cancelled', 'cancelled'), ('pending', 'pending review'), ('closed', 'done')
    ), default='open')

    assigned_to = models.ForeignKey(User, related_name='assigned_tasks', null=True, blank=True, on_delete=models.SET_NULL)

    created_by = models.ForeignKey(User, related_name='+', null=True, on_delete=models.SET_NULL)
    updated_by = models.ForeignKey(User, related_name='+', null=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def place_code(self):
        return self.country.code + '-' + self.locality.code if self.locality else self.country.code


class Workflow(models.Model):
    title = models.CharField(max_length=256, null=False, blank=False)
    description = models.TextField(null=True, blank=True)

    tasks = models.ManyToManyField(Task, related_name='workflows')


@receiver(post_save, sender=User)
def create_editor(sender, **kwargs):
    # create editor for user objects
    user = kwargs["instance"]
    if not hasattr(user, 'editor') and not kwargs.get('raw'):
        editor = Editor(user=user)
        # ensure there is a country
        editor.country = Country.objects.first()
        editor.save()
