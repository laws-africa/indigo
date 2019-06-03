import logging

from django.db.models import signals
from django.dispatch import receiver
from django.conf import settings
from actstream.models import Action
from templated_email import send_templated_mail

from indigo_api.models import Task

from django.contrib.contenttypes.models import ContentType
from django_comments.models import Comment
from django_comments.signals import comment_was_posted


log = logging.getLogger(__name__)


class Notifier(object):
    def send_task_notifications(self, action):
        task = action.action_object

        if action.verb == 'assigned':
            self.send_templated_email('task_assigned', [action.target], {
                'action': action,
                'task': task,
                'recipient': action.target,
            })

        elif action.verb == 'closed':
            if task.last_assigned_to and task.last_assigned_to != action.actor:
                self.send_templated_email('task_closed_submitter', [task.last_assigned_to], {
                    'action': action,
                    'task': action.action_object,
                    'recipient': task.last_assigned_to,
                })

    def notify_comment_posted(self, comment):
        """
        This function will be responsible for emailing members of a thread when
        a comment is posted on a task.
        """
        task_content_type = ContentType.objects.get_for_model(Task)

        if comment.content_type == task_content_type:
            task = Task.objects.get(id=comment.object_pk)
            task_comments = Comment.objects\
                .filter(content_type=task_content_type, object_pk=task.id)\
                .select_related('user')
            recipient_list = [c.user for c in task_comments]

            recipient_list.append(task.created_by_user)
            if task.assigned_to:
                recipient_list.append(task.assigned_to)
            if task.last_assigned_to:
                recipient_list.append(task.last_assigned_to)

            recipient_list = list(set(recipient_list))
            recipient_list.remove(comment.user)

            for user in recipient_list:
                self.send_templated_email('task_new_comment', [user], {
                    'task': task,
                    'recipient': user,
                    'comment': comment,
                })

    def send_templated_email(self, template_name, recipient_list, context, **kwargs):
        real_context = {
            'SITE_URL': settings.INDIGO_URL,
            'INDIGO_ORGANISATION': settings.INDIGO_ORGANISATION,
        }
        real_context.update(context)

        log.info("Sending templated email {} to {}".format(template_name, recipient_list))

        recipient_list = [user.email for user in recipient_list]

        return send_templated_mail(
            template_name=template_name,
            from_email=None,
            recipient_list=recipient_list,
            context=real_context,
            fail_silently=settings.INDIGO_EMAIL_FAIL_SILENTLY,
            **kwargs)


notifier = Notifier()


@receiver(signals.post_save, sender=Action)
def post_save_task(sender, instance, **kwargs):
    """ Send 'created' action to activity stream if new task
    """
    if kwargs['created']:
        if isinstance(instance.action_object, Task):
            notifier.send_task_notifications(instance)


@receiver(comment_was_posted, sender=Comment)
def post_comment_save_notification(sender, **kwargs):
    """
    Send email when a user comments on a task
    """
    if kwargs['comment']:
        notifier.notify_comment_posted(kwargs['comment'])
