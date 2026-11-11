from unittest.mock import patch

from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command
from django.test import TestCase

from indigo_api.models import Country
from indigo_social.badges import CountryBadge, PermissionBadge, badges


class BadgeSyncTestCase(TestCase):
    fixtures = ['languages_data', 'countries']

    def setUp(self):
        self.reset_badges()
        self.user = User.objects.create_user(username='badge-test')
        self.badge = badges.registry['editor']
        CountryBadge.create_all()

    def tearDown(self):
        self.reset_badges()

    def reset_badges(self):
        # Registry instances survive TestCase database rollbacks.
        for badge in badges.registry.values():
            if isinstance(badge, PermissionBadge):
                badge._group = None
                badge._perms = None

    def test_sync_permissions_without_scanning_users(self):
        group = self.badge.group()
        obsolete = Permission.objects.get(codename='delete_user', content_type__app_label='auth')
        group.permissions.set([obsolete])
        self.user.groups.add(group)
        awards = list(self.user.badges_earned.values_list('pk', flat=True))
        with patch.object(PermissionBadge, 'synch', side_effect=AssertionError), \
                patch.object(CountryBadge, 'synch', side_effect=AssertionError), \
                patch.object(User.objects, 'all', side_effect=AssertionError):
            call_command('sync_badge_permissions')
            call_command('sync_badge_permissions')
        self.assertSetEqual(set(group.permissions.all()), set(self.badge.get_permissions()))
        self.assertTrue(self.user.groups.filter(pk=group.pk).exists())
        self.assertEqual(list(self.user.badges_earned.values_list('pk', flat=True)), awards)

    def test_command_creates_empty_groups(self):
        call_command('sync_badge_permissions')
        for badge in badges.registry.values():
            if isinstance(badge, PermissionBadge):
                group = Group.objects.get(name=badge.group_name)
                self.assertSetEqual(set(group.permissions.all()), set(badge.get_permissions()))

    def test_group_changes(self):
        group = self.badge.group()
        for reverse in (False, True):
            relation = group.user_set if reverse else self.user.groups
            member = self.user if reverse else group
            relation.add(member)
            self.assertTrue(self.user.badges_earned.filter(slug=self.badge.slug).exists())
            relation.remove(member)
            self.assertFalse(self.user.badges_earned.filter(slug=self.badge.slug).exists())
            relation.add(member)
            relation.clear()
            self.assertFalse(self.user.badges_earned.filter(slug=self.badge.slug).exists())
            self.assertFalse(self.user.groups.filter(pk=group.pk).exists())

    def test_country_changes(self):
        country = Country.objects.first()
        slug = CountryBadge.badge_slug(country)
        badges.registry.pop(slug)
        for reverse in (False, True):
            relation = country.editors if reverse else self.user.editor.permitted_countries
            member = self.user.editor if reverse else country
            relation.add(member)
            self.assertTrue(self.user.badges_earned.filter(slug=slug).exists())
            relation.remove(member)
            self.assertFalse(self.user.badges_earned.filter(slug=slug).exists())
            relation.add(member)
            relation.clear()
            self.assertFalse(self.user.badges_earned.filter(slug=slug).exists())
            self.assertFalse(self.user.editor.permitted_countries.filter(pk=country.pk).exists())
