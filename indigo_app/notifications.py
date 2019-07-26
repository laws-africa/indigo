import logging

from allauth.account.signals import user_signed_up
from django.conf import settings
from django.core.mail import mail_admins
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django_comments.models import Comment
from django.dispatch import receiver
from templated_email import send_templated_mail
from background_task import background
from actstream.models import Action

from indigo.settings import INDIGO_ORGANISATION
from indigo_api.models import Task


log = logging.getLogger(__name__)


class Notifier(object):
    def notify_task_action(self, action):
        task = action.action_object

        if action.verb == 'assigned':
            self.send_templated_email('task_assigned', [action.target], {
                'action': action,
                'task': task,
                'recipient': action.target,
            })

        elif action.verb == Task.VERBS['unsubmit'] and action.target:
            self.send_templated_email('task_changes_requested', [action.target], {
                'action': action,
                'task': task,
                'recipient': action.target,
            })

        elif action.verb == Task.VERBS['close']:
            if task.submitted_by_user and task.submitted_by_user != action.actor:
                self.send_templated_email('task_closed_submitter', [task.submitted_by_user], {
                    'action': action,
                    'task': task,
                    'recipient': task.submitted_by_user,
                })

        elif action.verb == Task.VERBS['submit'] and task.reviewed_by_user:
            self.send_templated_email('task_resubmitted', [task.reviewed_by_user], {
                'action': action,
                'task': task,
                'recipient': task.reviewed_by_user,
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
            if task.submitted_by_user:
                recipient_list.append(task.submitted_by_user)

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
            fail_silently=settings.INDIGO.get('EMAIL_FAIL_SILENTLY'),
            **kwargs)

    def notify_admins_user_signed_up(self, user):
        """ Function to send emails to admins to notify them when a new user 
        signs up
        """
        subject = "New User Alert"
        message = """Hey there.
        
        We're just writing to let you know that a new user has signed up on {0} with the following details:

            Full name: {1}
            Username: {2}
            Email: {3}

        Thanks!""" \
        .format(INDIGO_ORGANISATION, user.get_full_name(), user.username, user.email)

        mail_admins(subject, message, fail_silently=False, connection=None,
                    html_message=None)


notifier = Notifier()


@background(queue='indigo')
def notify_task_action(action_id):
    try:
        notifier.notify_task_action(Action.objects.get(pk=action_id))
    except Task.DoesNotExist:
        log.warning("Action with id {} doesn't exist, ignoring".format(action_id))


@background(queue='indigo')
def notify_comment_posted(comment_id):
    try:
        notifier.notify_comment_posted(Comment.objects.get(pk=comment_id))
    except Comment.DoesNotExist:
        log.warning("Comment with id {} doesn't exist, ignoring".format(comment_id))


@receiver(user_signed_up, sender=User)
def user_sign_up_signal_handler(**kwargs):
    if kwargs['user']:
        notifier.notify_admins_user_signed_up(kwargs['user'])


if not settings.INDIGO.get('NOTIFICATION_EMAILS_BACKGROUND', False):
    # change background notification tasks to be synchronous
    notify_task_action = notify_task_action.now
    notify_comment_posted = notify_comment_posted.now
