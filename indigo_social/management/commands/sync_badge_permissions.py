from django.core.management.base import BaseCommand

from indigo_social.badges import PermissionBadge, badges


class Command(BaseCommand):
    help = "Synchronise code-owned badge group permissions without scanning users. Run after migrate."

    def handle(self, *args, **options):
        for badge in badges.registry.values():
            if isinstance(badge, PermissionBadge):
                # Refresh even if this process has already cached the group.
                badge.refresh_permissions()
