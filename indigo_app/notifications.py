from django.db.models import signals
from django.dispatch import receiver
from django.conf import settings
from actstream.models import Action
from templated_email import send_templated_mail

from indigo_api.models import Task


class Notifier(object):
    def send_task_notifications(self, action):
        if action.verb in ['assigned']:

            self.send_templated_email('task_assigned', [action.target.email],
                {
                    'action': action,
                    'task': action.action_object,
                    'recipient': action.target,
                },
            )

    def send_templated_email(self, template_name, recipient_list, context, **kwargs):
        defaults = {
            'SITE_URL': settings.INDIGO_URL,
            'INDIGO_ORGANISATION': settings.INDIGO_ORGANISATION,
        }
        defaults.update(context)

        return send_templated_mail(
            template_name=template_name,
            from_email=None,
            recipient_list=recipient_list,
            context=context,
            **kwargs)


notifier = Notifier()


@receiver(signals.post_save, sender=Action)
def post_save_task(sender, instance, **kwargs):
    """ Send 'created' action to activity stream if new task
    """
    if kwargs['created']:
        if isinstance(instance.action_object, Task):
            notifier.send_task_notifications(instance)
