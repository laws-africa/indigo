from django.contrib.auth.models import Permission, Group
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.signals import request_started

from pinax.badges.base import Badge, BadgeAwarded, BadgeDetail
from pinax.badges.registry import badges
from indigo_api.models import Country
from indigo_app.models import Editor


# monkey-patch the badge registry to make it easier to find badges
badges.registry = badges._registry


def perms_to_codes(perms):
    return set('%s.%s' % (p.content_type.app_label, p.codename) for p in perms)


class BaseBadge(Badge):
    multiple = False
    levels = [1]
    events = []
    can_award_manually = True
    nature = None
    css_class = ""

    def __init__(self):
        # hoop jumping to ensure that BadgeAward objects pick up the correct name
        # and description
        self.levels = [BadgeDetail(name=self.name, description=self.description)]
        super(Badge, self).__init__()

    def can_award(self, user, **kwargs):
        return not user.badges_earned.filter(slug=self.slug).exists()

    def award(self, user, **state):
        """ Should this badge be awarded? This is part of the pinax-badges API
        and is called by `possibly_award`.
        """
        if self.can_award(user, **state):
            self.grant(user)
            return BadgeAwarded()

    def unaward(self, user):
        """ Unaward all awards of this badge to a user.
        """
        n, _ = user.badges_earned.filter(slug=self.slug).delete()
        if n > 0:
            self.revoke(user)

    def grant(self, user):
        """ Grant this badge to a user.
        """
        pass

    def revoke(self, user):
        """ Revoke this badge from a user.
        """
        pass

    @property
    def image(self):
        return f"images/badges/{self.slug}.svg"


class PermissionBadge(BaseBadge):
    """ Description of a permissions-based badge, linked to a set of django permissions.

    When awarded, the user is give the appropriate permissions. When unawarded, the reverse happens.
    """
    permissions = ()
    group_name = None
    nature = 'permission'
    image = "images/badges/permission.svg"

    _perms = None
    _group = None

    def grant(self, user):
        """ Grant this badge's permissions to a user.
        """
        user.groups.add(self.group())

    def revoke(self, user):
        """ Revoke this badge's permissions from a user.
        """
        user.groups.remove(self.group())

    def group(self):
        """ Get the Group model this permission corresponds to.
        """
        if not self._group:
            assert self.group_name is not None
            self._group, created = Group.objects.get_or_create(name=self.group_name)
            self.refresh_permissions()

        return self._group

    def refresh_permissions(self):
        """ Ensure the permissions on the group are up to date.
        """
        self.group().permissions.add(*self.get_permissions())

    def get_permissions(self):
        """ Return a list of Permission objects for this badge.
        """
        if self._perms is None:
            perms = []
            for app_label, codename in (p.split('.', 2) for p in self.permissions):
                perm = Permission.objects.filter(codename=codename, content_type__app_label=app_label).first()
                if perm:
                    perms.append(perm)
            self._perms = perms

        return self._perms

    @classmethod
    def group_membership_changed(cls, user, groups, added):
        """ User group memberships have been added (or removed if added is False).
        Award/unaward badges if necessary.
        """
        group_names = [g.name for g in groups]
        for badge in (b for b in badges.registry.values() if isinstance(b, PermissionBadge) and b.group_name in group_names):
            if added:
                badge.possibly_award(user=user)
            else:
                badge.unaward(user)

    @classmethod
    def synch_grants(cls, user):
        """ Ensure users that have been awarded permissions badges, have all the
        right permissions. This is useful when the permissions have been changed.
        """
        for badge in (b for b in badges.registry.values() if isinstance(b, PermissionBadge)):
            if user.badges_earned.filter(slug=badge.slug).exists():
                badge.grant(user)

    @classmethod
    def synch(cls):
        """ Ensure all users have appropriate permissions badges.

        We do this by:
        1. ensuring the appropriate security groups exist, with the right permissions
        2. faking "adds" for all the users that aren't already part of the group, to ensure
           they get a badge.
        """
        for user in User.objects.all():
            # ensure users with badges are in the right security groups
            cls.synch_grants(user)

            # ensure users in the various security groups have the badge
            groups = user.groups.all()
            cls.group_membership_changed(user, groups, added=True)


@receiver(m2m_changed, sender=User.groups.through)
def groups_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    """ When user groups change, award or unaward any matching PermissionBadges
    as necessary.
    """
    if reverse or action not in ["post_add", "post_remove"]:
        return

    user = instance
    added = action == "post_add"
    groups = Group.objects.filter(pk__in=pk_set)
    PermissionBadge.group_membership_changed(user, groups, added)


class CountryBadge(BaseBadge):
    nature = 'country'
    image = "images/badges/country.svg"

    def grant(self, user):
        user.editor.permitted_countries.add(self.country)

    def revoke(self, user):
        user.editor.permitted_countries.remove(self.country)

    @property
    def name(self):
        return "Country: %s" % self.country.name

    @property
    def description(self):
        return "Can make changes to works for %s" % self.country.name

    @classmethod
    def badge_slug(cls, country):
        return 'country-' + country.code

    @classmethod
    def editor_countries_changed(cls, editor, countries, added):
        for country in countries:
            badge = badges.registry[cls.badge_slug(country)]
            if added:
                badge.possibly_award(user=editor.user)
            else:
                badge.unaward(editor.user)

    @classmethod
    def create_for_country(cls, country):
        class X(CountryBadge):
            pass

        X.country = country
        X.slug = cls.badge_slug(country)
        badges.register(X)

    @classmethod
    def create_all(cls):
        """ Ensure that country badges exist for each country.
        """
        for country in Country.objects.all():
            cls.create_for_country(country)

    @classmethod
    def synch(cls):
        """ Ensure all users have appropriate country badges.
        """
        for editor in Editor.objects.all():
            for country in editor.permitted_countries.all():
                badge = badges.registry[cls.badge_slug(country)]
                badge.possibly_award(user=editor.user)

            for badge in editor.user.badges_earned.filter():
                if isinstance(badge._badge, CountryBadge):
                    if badge.country not in editor.permitted_countries.all():
                        badge.unaward(editor.user)


@receiver(m2m_changed, sender=Editor.permitted_countries.through)
def editor_countries_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    """ When user's permitted countries change, award or unaward any matching CountryBadges
    as necessary.
    """
    if reverse or action not in ["post_add", "post_remove"]:
        return

    editor = instance
    added = action == "post_add"
    countries = model.objects.filter(pk__in=pk_set)
    CountryBadge.editor_countries_changed(editor, countries, added)


@receiver(post_save, sender=Country)
def country_saved(sender, instance, created, raw, **kwargs):
    if created:
        CountryBadge.create_for_country(instance)


def create_country_badges():
    # Install a once-off signal handler to create country badges before the
    # first request comes through. This allows us to work around the fact
    # that during testing, ready() is called before the database migrations
    # are applied, so no db tables exist. There doesn't seem to be a better
    # way to get code to run when the app starts up and AFTER the db has
    # been set up.
    uid = "indigo-social-country-setup"

    def create_badges(sender, **kwargs):
        request_started.disconnect(create_badges, dispatch_uid=uid)
        CountryBadge.create_all()

    request_started.connect(create_badges, dispatch_uid=uid, weak=False)
