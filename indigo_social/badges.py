from itertools import chain

from django.contrib.auth.models import Permission
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

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


class PermissionBadge(BaseBadge):
    """ Description of a permissions-based badge, linked to a set of django permissions.

    When awarded, the user is give the appropriate permissions. When unawarded, the reverse happens.
    """
    permissions = ()

    _perms = None

    def grant(self, user):
        """ Grant this badge's permissions to a user.
        """
        user.user_permissions.add(*self.get_permissions())

    def revoke(self, user):
        """ Revoke this badge's permissions from a user.
        """
        user.user_permissions.remove(*self.get_permissions())

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
    def permissions_changed(cls, user, perms, added):
        """ User permissions have been added (or removed if added is False).
        Award/unaward badges if necessary. If permissions have been removed,
        it doesn't mean the user doesn't have them any more since they may
        still be granted through groups.
        """
        for badge in (b for b in badges.registry.itervalues() if isinstance(b, PermissionBadge)):
            badge_perms = set(badge.permissions)

            # is this badge linked to the adjusted perms?
            if badge_perms & perms:
                existing = user.get_all_permissions()

                if existing & badge_perms == badge_perms:
                    if added:
                        badge.possibly_award(user=user)
                elif not added:
                    badge.unaward(user)

    @classmethod
    def synch_grants(cls, user):
        """ Ensure users that have been awarded permissions badges, have all the
        right permissions. This is useful when the permissions have been changed.
        """
        for badge in (b for b in badges.registry.itervalues() if isinstance(b, PermissionBadge)):
            if user.badges_earned.filter(slug=badge.slug).exists():
                badge.grant(user)

    @classmethod
    def synch(cls):
        """ Ensure all users have appropriate permissions badges.

        We do this by:
        1. ensuring users with badges are granted all the perms (this allows perms to be added)
        2. faking "adds" for all the perms each user has, which ensures new badges are granted.

        This means that if a user no longer has permissions granted by a badge, they don't lose
        the badge. Instead, they are granted the permissions.

        This allows us to add new perms to existing badges.
        """
        for user in User.objects.all():
            # ensure users badges are granted all the perms
            cls.synch_grants(user)

            # possibly grant new badges
            existing = user.get_all_permissions()
            cls.permissions_changed(user, existing, added=True)


@receiver(m2m_changed, sender=User.user_permissions.through)
def permissions_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    """ When user permissions change, award or unaward any matching PermissionBadges
    as necessary.
    """
    if reverse or action not in ["post_add", "post_remove"]:
        return

    user = instance
    added = action == "post_add"
    perms = perms_to_codes(model.objects.filter(pk__in=pk_set).prefetch_related('content_type').all())
    PermissionBadge.permissions_changed(user, perms, added)


@receiver(m2m_changed, sender=User.groups.through)
def groups_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    """ When user groups change, award or unaward any matching PermissionBadges
    as necessary.
    """
    if reverse or action not in ["post_add", "post_remove"]:
        return

    user = instance
    added = action == "post_add"
    groups = model.objects.filter(pk__in=pk_set).prefetch_related('permissions', 'permissions__content_type').all()
    perms = perms_to_codes(chain(*(g.permissions.all() for g in groups)))
    PermissionBadge.permissions_changed(user, perms, added)


class CountryBadge(BaseBadge):
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
    countries = model.objects.filter(pk__in=pk_set).all()
    CountryBadge.editor_countries_changed(editor, countries, added)


@receiver(post_save, sender=Country)
def country_saved(sender, instance, created, raw, **kwargs):
    if created:
        CountryBadge.create_for_country(instance)


# ------------------------------------------------------------------------
# Badge definitions


class ContributorBadge(PermissionBadge):
    slug = 'contributor'
    name = 'Contributor'
    description = 'Can view work details'
    permissions = ('indigo_api.view_work', 'indigo_api.add_annotation', 'indigo_api.change_annotation', 'indigo_api.delete_annotation')


class DrafterBadge(PermissionBadge):
    slug = 'drafter'
    name = 'Drafter'
    description = 'Can create new works and edit the details of existing works'
    permissions = ('indigo_api.add_work', 'indigo_api.change_work', 'indigo_api.add_document', 'indigo_api.change_document')


class SeniorDrafterBadge(PermissionBadge):
    slug = 'senior-drafter'
    name = 'Senior Drafter'
    description = 'Can review work tasks and delete documents and works'
    permissions = ('indigo_api.delete_work', 'indigo_api.review_work', 'indigo_api.review_document', 'indigo_api.delete_document')


badges.register(ContributorBadge)
badges.register(DrafterBadge)
badges.register(SeniorDrafterBadge)
