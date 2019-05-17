from django.db.models import signals
from django.dispatch import receiver
from django.conf import settings
from actstream.models import Action
from templated_email import send_templated_mail

from indigo_api.models import Task


@receiver(signals.post_save, sender=Action)
def post_save_task(sender, instance, **kwargs):
    """ Send 'created' action to activity stream if new task
    """
    if kwargs['created']:
        if isinstance(instance.action_object, Task):
            notifier.send_task_notifications(instance)


class Notifier(object):
    def send_task_notifications(self, action):
        if action.verb in ['assigned']:
            send_templated_mail(
                template_name='task_assigned',
                from_email=None,
                recipient_list=[action.target.email],
                context={
                    'action': action,
                    'task': action.action_object,
                    'recipient': action.target,
                    'site_url': settings.INDIGO_URL,
                },
            )


notifier = Notifier()