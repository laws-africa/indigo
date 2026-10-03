from unittest.mock import patch

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from django.test import TestCase

from indigo_social.models import retrieve_profile_photo_on_signup


class SocialSignupTestCase(TestCase):
    def test_google_signup_without_picture(self):
        user = User.objects.create_user(username='without-photo')
        account = SocialAccount.objects.create(user=user, provider='google', uid='google-user', extra_data={})

        with patch('indigo_social.models.retrieve_social_profile_photo') as retrieve_photo:
            for extra_data in ({}, {'picture': None}):
                account.extra_data = extra_data
                account.save(update_fields=['extra_data'])
                retrieve_profile_photo_on_signup(sender=User, user=user)

        retrieve_photo.assert_not_called()
        self.assertFalse(user.userprofile.profile_photo)

    def test_google_signup_with_picture(self):
        user = User.objects.create_user(username='with-photo')
        SocialAccount.objects.create(
            user=user, provider='google', uid='google-user', extra_data={'picture': 'https://example.com/photo.jpg'},
        )

        with patch('indigo_social.models.retrieve_social_profile_photo') as retrieve_photo:
            retrieve_profile_photo_on_signup(sender=User, user=user)

        retrieve_photo.assert_called_once_with(user.userprofile, 'https://example.com/photo.jpg')
