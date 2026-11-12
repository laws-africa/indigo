from unittest.mock import patch

from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command
from django.test import TestCase

from indigo_api.models import Country
from indigo_social.badges import CountryBadge, PermissionBadge, badges, perms_to_codes


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
        custom = Permission.objects.get(codename='view_group', content_type__app_label='auth')
        group.permissions.set([custom])
        self.user.groups.add(group)
        awards = list(self.user.badges_earned.values_list('pk', flat=True))
        with patch.object(PermissionBadge, 'synch', side_effect=AssertionError), \
                patch.object(CountryBadge, 'synch', side_effect=AssertionError), \
                patch.object(User.objects, 'all', side_effect=AssertionError):
            call_command('sync_badge_permissions')
            call_command('sync_badge_permissions')
        self.assertSetEqual(set(group.permissions.all()), set(self.badge.get_permissions()) | {custom})
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


class BadgePermissionsTestCase(TestCase):
    def setUp(self):
        self.reset_badges()
        self.addCleanup(self.reset_badges)
        self.badge = badges.registry['editor']

    @staticmethod
    def reset_badges():
        for badge in badges.registry.values():
            if isinstance(badge, PermissionBadge):
                badge._group = None
                badge._perms = None

    def test_restored_badge_permissions_survive_sync(self):
        expected = {
            'content-api': {'indigo_api.view_taxonomytopic'},
            'contributor': {
                'indigo_api.add_documentactivity', 'indigo_api.change_documentactivity',
                'indigo_api.delete_documentactivity', 'indigo_api.view_published_document',
            },
            'editor': {
                'indigo_api.view_work', 'indigo_api.view_commencement',
                'indigo_api.add_commencement', 'indigo_api.change_commencement',
                'indigo_api.delete_commencement',
            },
            'researcher': {
                'indigo_api.add_amendmentinstruction', 'indigo_api.change_amendmentinstruction',
                'indigo_api.delete_amendmentinstruction',
            },
            'super-reviewer': {
                'indigo_api.add_placesettings', 'indigo_api.change_placesettings',
                'indigo_api.delete_placesettings',
            },
        }
        for _ in range(2):
            call_command('sync_badge_permissions')
            for slug, permissions in expected.items():
                with self.subTest(badge=slug):
                    self.assertTrue(permissions <= perms_to_codes(badges.registry[slug].group().permissions.all()))

    def test_extend_permissions(self):
        badge = self.badge
        original_permissions = badge.permissions
        self.addCleanup(setattr, badge, 'permissions', original_permissions)
        badge.get_permissions()
        for _ in range(2):
            badges.extend_permissions('editor', ('auth.view_group',))
        self.assertIsNone(badge._perms)
        self.assertEqual(badge.permissions.count('auth.view_group'), 1)
        badge.refresh_permissions()
        self.assertIn('auth.view_group', perms_to_codes(badge.group().permissions.all()))

    def test_sync_preserves_custom_permissions_and_restores_defaults(self):
        group = self.badge.group()
        custom = Permission.objects.get(codename='view_group', content_type__app_label='auth')
        group.permissions.set([custom])
        # Exercise the first group lookup as well as subsequent command refreshes.
        self.badge._group = None
        self.badge.group()
        for _ in range(2):
            call_command('sync_badge_permissions')
            self.assertSetEqual(set(group.permissions.all()), set(self.badge.get_permissions()) | {custom})
