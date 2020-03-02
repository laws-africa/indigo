from django.dispatch import receiver
from django.contrib.auth.models import User
from allauth.account.signals import user_signed_up

from indigo_social.badges import PermissionBadge, badges


# ------------------------------------------------------------------------
# Default Badge definitions
#
# You can define your own badges, either in addition to these (in your
# own module), or in favour of these (by changing settings.INDIGO_SOCIAL['badges']
# to the module name. The badges will be imported when the app starts up.


class ContributorBadge(PermissionBadge):
    slug = 'contributor'
    name = 'Contributor'
    group_name = name + ' Badge'
    description = 'Can view work details'
    permissions = ('indigo_api.add_annotation', 'indigo_api.change_annotation', 'indigo_api.delete_annotation',
                   'indigo_api.add_task')


class DrafterBadge(PermissionBadge):
    slug = 'drafter'
    name = 'Drafter'
    group_name = name + ' Badge'
    description = 'Can create new works and edit the details of existing works'
    permissions = ('indigo_api.add_work', 'indigo_api.change_work',
                   'indigo_api.add_document', 'indigo_api.change_document',
                   'indigo_api.add_documentactivity', 'indigo_api.change_documentactivity', 'indigo_api.delete_documentactivity',
                   'indigo_api.add_amendment', 'indigo_api.change_amendment', 'indigo_api.delete_amendment',
                   # required when restoring a document version
                   'reversion.add_version', 'reversion.change_version',
                   'indigo_api.change_task', 'indigo_api.submit_task', 'indigo_api.reopen_task',
                   'indigo_api.add_workflow', 'indigo_api.change_workflow')


class SeniorDrafterBadge(PermissionBadge):
    slug = 'senior-drafter'
    name = 'Senior Drafter'
    group_name = name + ' Badge'
    description = 'Can review work tasks and delete documents and works'
    permissions = ('indigo_api.bulk_add_work', 'indigo_api.delete_work', 'indigo_api.review_work', 'indigo_api.bulk_export_work',
                   'indigo_api.add_commencement', 'indigo_api.change_commencement', 'indigo_api.delete_commencement',
                   'indigo_api.review_document', 'indigo_api.delete_document', 'indigo_api.publish_document',
                   'indigo_api.add_placesettings', 'indigo_api.change_placesettings', 'indigo_api.delete_placesettings',
                   'indigo_api.cancel_task', 'indigo_api.unsubmit_task', 'indigo_api.close_task',
                   'indigo_api.close_workflow', 'indigo_api.delete_workflow')


badges.register(ContributorBadge)
badges.register(DrafterBadge)
badges.register(SeniorDrafterBadge)


# when a user signs up, grant them the contributor badge immediately
@receiver(user_signed_up, sender=User)
def grant_contributor_new_user(sender, request, user, **kwargs):
    badges.registry['contributor'].award(user=user)
