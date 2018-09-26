from django.contrib.auth.models import Permission

from pinax.badges.base import Badge, BadgeAwarded, BadgeDetail
from pinax.badges.registry import badges


class PermissionBadge(Badge):
    """ Description of a permissions-based badge, linked to a set of django permissions.

    When awarded, the user is give the appropriate permissions. When unawarded, the reverse happens.
    """
    permissions = ()
    multiple = False
    levels = [1]
    events = []

    _perms = None

    def __init__(self):
        # hoop jumping to ensure that BadgeAward objects pick up the correct name
        # and description
        self.levels = [BadgeDetail(name=self.name, description=self.description)]
        super(PermissionBadge, self).__init__()

    def can_award(self, user):
        return not user.badges_earned.filter(slug=self.slug).exists()

    def award(self, user, **state):
        """ Should this badge be awarded? This is part of the pinax-badges API
        and is called by `possibly_award`.
        """
        if self.can_award(user):
            self.grant(user)
            return BadgeAwarded()

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


class ContributorBadge(PermissionBadge):
    slug = 'contributor'
    name = 'Contributor'
    description = 'Can view work details'
    permissions = ('indigo_api.view_work',)


class DrafterBadge(PermissionBadge):
    slug = 'drafter'
    name = 'Drafter'
    description = 'Can create new works and edit the details of existing works'
    permissions = ('indigo_api.add_work', 'indigo_api.change_work')


class SeniorDrafterBadge(PermissionBadge):
    slug = 'senior-drafter'
    name = 'Senior Drafter'
    description = 'Can review work tasks and delete documents and works'
    permissions = ('indigo_api.delete_work', 'indigo_api.review_work', 'indigo_api.delete_document')


badges.register(ContributorBadge)
badges.register(DrafterBadge)
badges.register(SeniorDrafterBadge)
# monkey-patch the badge registry to make it easier to find badges
badges.registry = badges._registry

# TODO: trigger when user permissions change
