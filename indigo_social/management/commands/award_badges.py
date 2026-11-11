from django.core.management.base import BaseCommand

from indigo_social.badges import PermissionBadge, CountryBadge


class Command(BaseCommand):
    help = 'Repair badge awards and access for all users; not required on deployment'

    def handle(self, *args, **options):
        PermissionBadge.synch()

        CountryBadge.create_all()
        CountryBadge.synch()
