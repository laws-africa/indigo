from django.db.models import signals
from django.dispatch import receiver

from actstream.models import Action
from django_comments.models import Comment
from django_comments.signals import comment_was_posted

from indigo_api.models import Task
from indigo_app.notifications import send_task_notifications, notify_comment_posted


@receiver(signals.post_save, sender=Action)
def task_action_created(sender, instance, **kwargs):
    """ Send 'created' action to activity stream if new task
    """
    if kwargs['created']:
        if isinstance(instance.action_object, Task):
            send_task_notifications(instance.pk)


@receiver(comment_was_posted, sender=Comment)
def post_comment_save_notification(sender, **kwargs):
    """ Send email when a user comments on a task
    """
    if kwargs['comment']:
        notify_comment_posted(kwargs['comment'].pk)
