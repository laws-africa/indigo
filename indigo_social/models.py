import random
import string
from urllib.request import urlretrieve, urlcleanup

from allauth.account.signals import user_signed_up
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.core.files import File
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


def user_profile_photo_path(instance, filename):
    if instance.id is not None:
        return 'avatars/{}'.format(instance.id)
    raise ValueError


def retrieve_social_profile_photo(user_profile, url):
    """ Retrieve and save a retrieved user's profile photo from a url
    """
    try:
        filename, _ = urlretrieve(url)
        user_profile.profile_photo.save(filename, File(open(filename, 'rb')))
        user_profile.generate_nonce()
        user_profile.save()
    finally:
        urlcleanup()


class UserProfile(models.Model):
    class Meta:
        permissions = (('audit_user_activity', 'Can audit user activity'),)

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("user"))
    bio = models.TextField(_("bio"), blank=True, null=True, default='', help_text=_("A short bio"))
    qualifications = models.TextField(_("qualifications"), blank=True, null=True, default='', help_text=_("Qualifications"))
    skills = models.TextField(_("skills"), blank=True, null=True, default='', help_text=_("Skills"))
    organisations = models.TextField(_("organisations"), blank=True, null=True, default='', help_text=_("Organisations"))
    specialisations = models.TextField(_("specialisations"), blank=True, null=True, default='', help_text=_("Specialisations"))
    areas_of_law = models.CharField(_("areas of law"), max_length=256, blank=True, null=True, default='', help_text=_("Areas of law"))
    profile_photo = models.ImageField(_("profile photo"), upload_to=user_profile_photo_path, blank=True, null=True)
    profile_photo_nonce = models.CharField(_("profile photo nonce"), max_length=256, blank=True, null=True)
    twitter_username = models.CharField(_("twitter username"), max_length=256, blank=True, null=True, default='')
    linkedin_profile = models.URLField(_("linkedin profile"), blank=True, null=True, default='')

    def generate_nonce(self):
        self.profile_photo_nonce = ''.join(random.sample(string.ascii_lowercase, 8))

    @property
    def profile_photo_url(self):
        if not self.profile_photo:
            return static('images/avatars/default_avatar.svg')
        return reverse('indigo_social:user_profile_photo', kwargs={'username': self.user.username, 'nonce': self.profile_photo_nonce})


@receiver(post_save, sender=User)
def create_user_profile(sender, **kwargs):
    # create a user profile for each new user object
    user = kwargs["instance"]
    if not hasattr(user, "userprofile") and not kwargs.get("raw"):
        user_profile = UserProfile(user=user)
        user_profile.save()


@receiver(user_signed_up, sender=User)
def retrieve_profile_photo_on_signup(sender, **kwargs):
    user = kwargs['user']

    try:
        user_social_account = SocialAccount.objects.get(user=user, provider='google')
        url = user_social_account.extra_data.get('picture')
        retrieve_social_profile_photo(user.userprofile, url)

    except (SocialAccount.DoesNotExist, UserProfile.DoesNotExist):
        pass


class BadgeAward(models.Model):
    user = models.ForeignKey(User, related_name="badges_earned", on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)
    slug = models.CharField(max_length=255)
    level = models.IntegerField(default=1)

    class Meta:
        db_table = "pinax_badges_badgeaward"

    def __getattr__(self, attr):
        return getattr(self._badge, attr)

    @property
    def badge(self):
        return self

    @property
    def _badge(self):
        from indigo_social.badges import badges
        return badges.registry[self.slug]
