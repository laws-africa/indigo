from django.contrib.auth.models import User
from django.db.models import signals
from django.dispatch import receiver

from allauth.account.signals import user_signed_up
from actstream.models import Action
from django_comments.models import Comment
from django_comments.signals import comment_was_posted
from pinax.badges.signals import badge_awarded

from indigo_api.models import Task, Annotation
from indigo_app.notifications import notify_task_action, notify_comment_posted, notify_new_user_signed_up, notify_annotation_reply_posted, notify_user_badge_earned


@receiver(signals.post_save, sender=Action)
def task_action_created(sender, instance, **kwargs):
    """ Send 'created' action to activity stream if new task
    """
    if kwargs['created']:
        if isinstance(instance.action_object, Task):
            notify_task_action(instance.pk)


@receiver(comment_was_posted, sender=Comment)
def post_comment_save_notification(sender, **kwargs):
    """ Send email when a user comments on a task
    """
    if kwargs['comment']:
        notify_comment_posted(kwargs['comment'].pk)


@receiver(user_signed_up, sender=User)
def user_sign_up_signal_handler(**kwargs):
    """ Send an email to the admins when a new user signs up
    """
    if kwargs['user']:
        notify_new_user_signed_up(kwargs['user'].pk)


@receiver(signals.post_save, sender=Annotation)
def post_annotation_reply(sender, **kwargs):
    if kwargs['instance'].in_reply_to:
        notify_annotation_reply_posted(kwargs['instance'].pk)

@receiver(badge_awarded)
def post_badge_earned(sender, **kwargs):
    if kwargs.get('badge_award') and not kwargs['badge_award'].can_award_manually:
        notify_user_badge_earned(kwargs['badge_award'].pk)
