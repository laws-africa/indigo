import datetime
import logging
from itertools import groupby

from actstream import action
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import ugettext_lazy as _
from django.db.models import JSONField
from django.db import models
from django.db.models import signals, Prefetch, Count
from django.conf import settings
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.utils import timezone
from allauth.account.utils import user_display
from django_fsm import FSMField, has_transition_perm, transition
from django_fsm.signals import post_transition

from indigo.custom_tasks import tasks as custom_tasks
from indigo.plugins import plugins
from indigo_api.models import Document
from indigo_api.signals import task_closed

log = logging.getLogger(__name__)


class TaskQuerySet(models.QuerySet):
    def unclosed(self):
        return self.filter(state__in=Task.OPEN_STATES)

    def closed(self):
        return self.filter(state__in=Task.CLOSED_STATES)


class TaskManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        from .works import Work
        from .documents import Document

        return super(TaskManager, self).get_queryset() \
            .select_related('created_by_user', 'updated_by_user', 'assigned_to',
                            'submitted_by_user', 'reviewed_by_user', 'country',
                            'country__country', 'locality', 'locality__country', 'locality__country__country') \
            .prefetch_related(Prefetch('work', queryset=Work.objects.filter())) \
            .prefetch_related(Prefetch('document', queryset=Document.objects.no_xml())) \
            .prefetch_related('labels')


class Task(models.Model):
    OPEN = 'open'
    ASSIGNED = 'assigned'
    PENDING_REVIEW = 'pending_review'
    CANCELLED = 'cancelled'
    DONE = 'done'
    BLOCKED = 'blocked'

    STATES = (OPEN, PENDING_REVIEW, CANCELLED, DONE, BLOCKED)

    CLOSED_STATES = (CANCELLED, DONE)
    OPEN_STATES = (OPEN, BLOCKED, PENDING_REVIEW)
    UNBLOCKED_STATES = (OPEN, PENDING_REVIEW)

    STATE_CHOICES = [
        (BLOCKED, _('Blocked')),
        (OPEN, _('Open')),
        (ASSIGNED, _('Assigned')),
        (PENDING_REVIEW, _('Pending review')),
        (DONE, _('Done')),
        (CANCELLED, _('Cancelled')),
    ]

    VERBS = {
        'submit': 'submitted',
        'cancel': 'cancelled',
        'reopen': 'reopened',
        'unsubmit': 'requested changes to',
        'close': 'approved',
        'finish': 'finished',
        'block': 'blocked',
        'unblock': 'unblocked',
    }

    MAIN_CODES = [
        ('convert-document', _('Convert document')),
        ('import-content', _('Import content')),
        ('apply-amendment', _('Apply amendment')),
        ('link-gazette', _('Link gazette')),
    ]

    CODES = MAIN_CODES + [
        ('check-update-primary', _('Check / update primary work')),
        ('check-update-repeal', _('Check / update repeal')),
        ('commences-on-date-missing', _("'Commences on' date missing")),
        ('link-amendment-active', _('Link amendment (active)')),
        ('link-amendment-passive', _('Link amendment (passive)')),
        ('link-amendment-pending-commencement', _('Link amendment (pending commencement)')),
        ('link-commencement-active', _('Link commencement (active)')),
        ('link-commencement-passive', _('Link commencement (passive)')),
        ('link-primary-work', _('Link primary work')),
        ('link-repeal', _('Link repeal')),
        ('no-repeal-match', _('Link repeal (not found)')),
        ('link-repeal-pending-commencement', _('Link repeal (pending commencement)')),
        ('link-subleg', _('Link subleg')),
        ('link-taxonomy', _('Link taxonomy')),
        ('review-work-expression', _('Sign-off')),
    ]

    class Meta:
        permissions = (
            ('submit_task', _('Can submit an open task for review')),
            ('cancel_task', _('Can cancel a task that is open or has been submitted for review')),
            ('reopen_task', _('Can reopen a task that is closed or cancelled')),
            ('unsubmit_task', _('Can unsubmit a task that has been submitted for review')),
            ('close_task', _('Can close a task that has been submitted for review')),
            ('close_any_task', _('Can close any task that has been submitted for review, regardless of who submitted it')),
            ('block_task', _('Can block a task from being done, and unblock it')),
            ('exceed_task_limits', _('Can be assigned tasks in excess of limits')),
        )
        verbose_name = _('task')
        verbose_name_plural = _('tasks')

    objects = TaskManager.from_queryset(TaskQuerySet)()

    title = models.CharField(_('title'), max_length=256, null=False, blank=False)
    description = models.TextField(_('description'), null=True, blank=True)

    country = models.ForeignKey('indigo_api.Country', verbose_name=_('country'), related_name='tasks', null=False, blank=False, on_delete=models.CASCADE)
    locality = models.ForeignKey('indigo_api.Locality', verbose_name=_('locality'), related_name='tasks', null=True, blank=True, on_delete=models.CASCADE)
    work = models.ForeignKey('indigo_api.Work', verbose_name=_('work'), related_name='tasks', null=True, blank=True, on_delete=models.CASCADE)
    document = models.ForeignKey('indigo_api.Document', verbose_name=_('document'), related_name='tasks', null=True, blank=True, on_delete=models.CASCADE)
    timeline_date = models.DateField(_('timeline date'), null=True, blank=True, help_text=_("A date on the timeline of work-related tasks, e.g. the date at which an amendment should be applied."))

    state = FSMField(_('state'), default=OPEN)

    # internal task code
    code = models.CharField(_('code'), max_length=100, null=True, blank=True)

    # files
    input_file = models.OneToOneField('TaskFile', verbose_name=_('input file'), related_name='task_as_input', null=True, blank=True, on_delete=models.SET_NULL)
    output_file = models.OneToOneField('TaskFile', verbose_name=_('output file'), related_name='task_as_output', null=True, blank=True, on_delete=models.SET_NULL)

    assigned_to = models.ForeignKey(User, verbose_name=_('assigned to'), related_name='assigned_tasks', null=True, blank=True, on_delete=models.SET_NULL)
    submitted_by_user = models.ForeignKey(User, verbose_name=_('submitted by user'), related_name='submitted_tasks', null=True, blank=True, on_delete=models.SET_NULL)
    reviewed_by_user = models.ForeignKey(User, verbose_name=_('reviewed by user'), related_name='reviewed_tasks', null=True, on_delete=models.SET_NULL)
    finished_by_user = models.ForeignKey(User, verbose_name=_('finished by user'), related_name='finished_tasks', null=True, on_delete=models.SET_NULL)
    closed_at = models.DateTimeField(_('closed at'), help_text=_("When the task was marked as done or cancelled."), null=True)

    changes_requested = models.BooleanField(_('changes requested'), default=False, help_text=_("Have changes been requested on this task?"))

    created_by_user = models.ForeignKey(User, verbose_name=_('created by user'), related_name='+', null=True, on_delete=models.SET_NULL)
    updated_by_user = models.ForeignKey(User, verbose_name=_('updated by user'), related_name='+', null=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    labels = models.ManyToManyField('TaskLabel', verbose_name=_('labels'), related_name='tasks')

    extra_data = JSONField(_('extra data'), null=True, blank=True)

    blocked_by = models.ManyToManyField('self', verbose_name=_('blocked by'), related_name='blocking', symmetrical=False, help_text=_('Tasks blocking this task from being done.'))

    @property
    def place(self):
        return self.locality or self.country

    @property
    def is_closed(self):
        return self.state in self.CLOSED_STATES

    @property
    def is_open(self):
        return self.state in self.OPEN_STATES

    def clean(self):
        # enforce that any work and/or document are for the correct place
        if self.document and self.document.work != self.work:
            self.document = None

        if self.work and (self.work.country != self.country or self.work.locality != self.locality):
            self.work = None

    def can_assign_to(self, user):
        """ Can this task be assigned to this user?
        """
        return user.editor.permitted_countries.filter(pk=self.country.pk).exists()

    def assign_to(self, assignee, assigned_by):
        """ Assign this task to assignee (may be None)
        """
        self.assigned_to = assignee
        self.save()
        if assigned_by == self.assigned_to:
            action.send(self.assigned_to, verb='picked up', action_object=self,
                        place_code=self.place.place_code)
        elif assignee:
            action.send(assigned_by, verb='assigned', action_object=self,
                        target=self.assigned_to,
                        place_code=self.place.place_code)
        else:
            action.send(assigned_by, verb='unassigned', action_object=self,
                        place_code=self.place.place_code)

    @classmethod
    def decorate_potential_assignees(cls, tasks, country, current_user):
        permitted_users = User.objects \
            .filter(editor__permitted_countries=country) \
            .order_by('first_name', 'last_name') \
            .all()
        potential_assignees = [u for u in permitted_users if u.has_perm('indigo_api.submit_task')]
        potential_reviewers = [u for u in permitted_users if u.has_perm('indigo_api.close_task') or u.has_perm('indigo_api.close_any_task')]

        for task in tasks:
            if task.state == 'open':
                task.potential_assignees = [u for u in potential_assignees if task.assigned_to_id != u.id]
            elif task.state == 'pending_review':
                task.potential_assignees = [u for u in potential_reviewers if task.assigned_to_id != u.id and
                                            (u.has_perm('indigo_api.close_any_task') or task.submitted_by_user_id != u.id)]
            else:
                task.potential_assignees = []

            # move the current user first
            if task.potential_assignees and current_user and current_user.is_authenticated:
                task.potential_assignees.sort(key=lambda u: 0 if u.id == current_user.id else 1)

        # mark users that have too many tasks
        cls.decorate_user_task_limits(set(u for task in tasks for u in task.potential_assignees), tasks)

        return tasks

    @classmethod
    def decorate_user_task_limits(cls, users, tasks):
        """ Count assigned tasks for these users and decorate users that have exceeded their threshold.
        """
        states = set(t.state for t in tasks)
        counts = Task.objects \
            .filter(assigned_to__in=users, state__in=states) \
            .values('assigned_to') \
            .annotate(tasks=Count(1))
        counts = {c['assigned_to']: c['tasks'] for c in counts}

        for user in users:
            user.assigned_tasks_count = counts.get(user.id, 0)
            user.too_many_tasks = (
                    user.assigned_tasks_count > settings.INDIGO['MAX_ASSIGNED_TASKS']
                    and not user.has_perm('indigo_api.exceed_task_limits'))

    @classmethod
    def decorate_permissions(cls, tasks, user):
        for task in tasks:
            task.change_task_permission = user.has_perm('indigo_api.change_task') and user.editor.has_country_permission(task.country)
            task.submit_task_permission = has_transition_perm(task.submit, user)
            task.finish_task_permission = has_transition_perm(task.finish, user)
            task.reopen_task_permission = has_transition_perm(task.reopen, user)
            task.unsubmit_task_permission = has_transition_perm(task.unsubmit, user)
            task.close_task_permission = has_transition_perm(task.close, user)

        return tasks

    @classmethod
    def decorate_submission_message(cls, tasks, view):
        for task in tasks:
            submission_message = _('Are you sure you want to submit this task for review?')
            if task.assigned_to and not task.assigned_to == view.request.user:
                submission_message = _('Are you sure you want to submit this task for review on behalf of %s?') % \
                    user_display(task.assigned_to)
            task.submission_message = submission_message

        return tasks

    # submit for review
    def may_submit(self, user):
        if user.has_perm('indigo_api.close_task'):
            senior_or_assignee = True
        else:
            senior_or_assignee = user == self.assigned_to

        return senior_or_assignee and \
               user.is_authenticated and \
               user.editor.has_country_permission(self.country) and \
               user.has_perm('indigo_api.submit_task')

    @transition(field=state, source=['open'], target='pending_review', permission=may_submit)
    def submit(self, user, **kwargs):
        if not self.assigned_to:
            self.assign_to(user, user)
        self.submitted_by_user = self.assigned_to
        self.assigned_to = self.reviewed_by_user

    # cancel
    def may_cancel(self, user):
        return user.is_authenticated and \
               user.editor.has_country_permission(self.country) and \
               user.has_perm('indigo_api.cancel_task')

    @transition(field=state, source=['open', 'pending_review', 'blocked'], target='cancelled', permission=may_cancel)
    def cancel(self, user):
        self.changes_requested = False
        self.assigned_to = None
        self.closed_at = timezone.now()
        self.update_blocked_tasks(self, user)

    # reopen – moves back to 'open'
    def may_reopen(self, user):
        return user.is_authenticated and \
               user.editor.has_country_permission(self.country) and \
               user.has_perm('indigo_api.reopen_task')

    @transition(field=state, source=['cancelled', 'done'], target='open', permission=may_reopen)
    def reopen(self, user, **kwargs):
        self.reviewed_by_user = None
        self.closed_at = None
        # re-block import task if conversion task is reopened
        if self.code in ['convert-document'] and self.timeline_date:
            import_task = Task.objects.filter(work=self.work, code='import-content', timeline_date=self.timeline_date).first()
            if import_task:
                import_task.blocked_by.add(self)
                if import_task.state in Task.UNBLOCKED_STATES:
                    import_task.block(user)

    # unsubmit – moves back to 'open'
    def may_unsubmit(self, user):
        return user.is_authenticated and \
               user.editor.has_country_permission(self.country) and \
               user.has_perm('indigo_api.unsubmit_task') and \
               (user == self.assigned_to or not self.assigned_to)

    @transition(field=state, source=['pending_review'], target='open', permission=may_unsubmit)
    def unsubmit(self, user, **kwargs):
        if not self.assigned_to or self.assigned_to != user:
            self.assign_to(user, user)
        self.reviewed_by_user = self.assigned_to
        self.assigned_to = self.submitted_by_user
        self.changes_requested = True

    # close
    def may_close(self, user):
        return user.is_authenticated and \
               user.editor.has_country_permission(self.country) and \
               (user.has_perm('close_any_task') or
                (user.has_perm('indigo_api.close_task') and
                 (user == self.assigned_to or
                  (not self.assigned_to and self.submitted_by_user != user))))

    @transition(field=state, source=['pending_review'], target='done', permission=may_close)
    def close(self, user, **kwargs):
        if not self.assigned_to or self.assigned_to != user:
            self.assign_to(user, user)
        self.reviewed_by_user = self.assigned_to
        self.closed_at = timezone.now()
        self.changes_requested = False
        self.assigned_to = None
        self.update_blocked_tasks(self, user)

        # send task_closed signal
        task_closed.send(sender=self.__class__, task=self)

    # finish (skip submission)
    def may_finish(self, user):
        return user.is_authenticated and \
               user.editor.has_country_permission(self.country) and \
               user.has_perm('indigo_api.submit_task')

    @transition(field=state, source=['open'], target='done', permission=may_finish)
    def finish(self, user, **kwargs):
        self.finished_by_user = user
        self.closed_at = timezone.now()
        self.changes_requested = False
        self.assigned_to = None

        # if a conversion task has been finished, do the import
        if self.code in ['convert-document'] and self.work is not None:
            self.create_and_import_document(user)

        self.update_blocked_tasks(self, user)

    def create_and_import_document(self, user):
        # create the document
        document = Document()
        document.work = self.work
        document.expression_date = self.timeline_date or self.work.get_import_date()
        document.language = self.country.primary_language
        document.created_by_user = user
        document.save()

        # link it to the related import task
        import_task = Task.objects.filter(work=self.work, code='import-content',
                                          timeline_date=self.timeline_date or self.work.get_import_date()).first()
        if import_task:
            import_task.document = document
            import_task.save()

        # do the import
        importer = plugins.for_document('importer', document)
        upload = UploadedFile(file=self.output_file.file, name=self.output_file.filename, size=self.output_file.size,
                              content_type=self.output_file.mime_type)
        try:
            importer.import_from_upload(upload, document, None)
        except ValueError as e:
            if document.pk:
                document.delete()
            log.error(f"Error during import: {e}", exc_info=e)

        document.updated_by_user = user
        document.save_with_revision(user)

    # block
    def may_block(self, user):
        return user.is_authenticated and \
               user.editor.has_country_permission(self.country) and \
               user.has_perm('indigo_api.block_task')

    @transition(field=state, source=['open', 'pending_review'], target='blocked', permission=may_block)
    def block(self, user, **kwargs):
        if self.assigned_to:
            self.assign_to(None, user)

    # unblock
    def may_unblock(self, user):
        return user.is_authenticated and \
               user.editor.has_country_permission(self.country) and \
               user.has_perm('indigo_api.block_task') and \
               (not self.blocked_by.exists())

    @transition(field=state, source=['blocked'], target='open', permission=may_unblock)
    def unblock(self, user, **kwargs):
        pass

    def update_blocked_tasks(self, task, user):
        # don't try to change m2m relationship on tasks that haven't been saved yet
        if task.pk:
            blocked_tasks = list(task.blocking.all())
            # this task is no longer blocking other tasks
            task.blocking.clear()
            for blocked_task in blocked_tasks:
                action.send(user, verb='resolved a task previously blocking', action_object=blocked_task,
                            target=task, place_code=blocked_task.place.place_code)

                # send a separate action to this task about it (partially) unblocking the previously blocked task
                # while we still have both of them available (the usual actions are sent post transition, when they
                # won't be linked anymore)
                action_verb = 'partially unblocked'

                if task.code in ['convert-document'] and blocked_task.code in ['import-content']:
                    blocked_task.unblock(user)
                    action_verb = self.VERBS['unblock']

                action.send(user, verb=action_verb, action_object=task,
                            target=blocked_task, place_code=task.place.place_code)

    def resolve_anchor(self):
        if self.annotation:
            return self.annotation.resolve_anchor()

    @property
    def customised(self):
        """ If this task is customised, return a new object describing the customisation.
        """
        if self.code:
            if not hasattr(self, '_customised'):
                plugin = custom_tasks.for_locale(self.code, country=self.country, locality=self.locality)
                self._customised = plugin
                if plugin:
                    self._customised.setup(self)
            return self._customised

    @classmethod
    def task_columns(cls, required_groups, tasks):
        def grouper(task):
            if task.state == 'open' and task.assigned_to:
                return 'assigned'
            else:
                return task.state

        state_choices = dict(cls.STATE_CHOICES)
        tasks = sorted(tasks, key=grouper)
        tasks = {state: list(group) for state, group in groupby(tasks, key=grouper)}

        # base columns on the requested task states
        groups = {}
        for key in required_groups:
            groups[key] = {
                'title': state_choices[key],
                'badge': key,
            }

        for key, group in tasks.items():
            if key not in groups:
                groups[key] = {
                    'title': state_choices[key],
                    'badge': key,
                }
            groups[key]['tasks'] = group

        # enforce column ordering
        return [groups.get(g) for g in ['blocked', 'open', 'assigned', 'pending_review', 'done', 'cancelled'] if g in groups]

    def get_extra_data(self):
        if self.extra_data is None:
            self.extra_data = {}
        return self.extra_data

    @property
    def friendly_state(self):
        return dict(self.STATE_CHOICES).get(self.state, '')


@receiver(signals.post_save, sender=Task)
def post_save_task(sender, instance, **kwargs):
    """ Send 'created' action to activity stream if new task
    """
    if kwargs['created']:
        action.send(instance.created_by_user, verb='created', action_object=instance,
                    place_code=instance.place.place_code)


@receiver(post_transition, sender=Task)
def post_task_transition(sender, instance, name, **kwargs):
    """ When tasks transition, store actions.

    Doing this in a signal, rather than in the transition method on the class,
    means that the task's state field is up to date. Our notification system
    is triggered on action signals, and the action objects passed to action
    signals are loaded fresh from the DB - so any objects they reference
    are also loaded from the db. So we ensure that the task is saved to the
    DB (including the updated state field), just before creating the action
    signal.
    """
    if name in instance.VERBS:
        user = kwargs['method_args'][0]
        comment = kwargs['method_kwargs'].get('comment', None)

        # ensure the task object changes are in the DB, since action signals
        # load related data objects from the db
        instance.save()

        if name == 'unsubmit':
            action.send(user, verb=instance.VERBS['unsubmit'],
                        action_object=instance,
                        target=instance.assigned_to,
                        place_code=instance.place.place_code,
                        comment=comment)
        else:
            action.send(user, verb=instance.VERBS[name],
                        action_object=instance,
                        place_code=instance.place.place_code,
                        comment=comment)


class WorkflowQuerySet(models.QuerySet):
    def unclosed(self):
        return self.filter(closed=False)

    def closed(self):
        return self.filter(closed=True)


class WorkflowManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return super(WorkflowManager, self).get_queryset() \
            .select_related('created_by_user')


class Workflow(models.Model):
    class Meta:
        permissions = (
            ('close_workflow', _('Can close a workflow')),
        )
        ordering = ('-priority', 'pk',)
        verbose_name = _('workflow')
        verbose_name_plural = _('workflows')

    objects = WorkflowManager.from_queryset(WorkflowQuerySet)()

    title = models.CharField(_('title'), max_length=256, null=False, blank=False)
    description = models.TextField(_('description'), null=True, blank=True)

    tasks = models.ManyToManyField(Task, verbose_name=_('tasks'), related_name='workflows')

    closed = models.BooleanField(_('closed'), default=False)
    due_date = models.DateField(_('due date'), null=True, blank=True)
    priority = models.BooleanField(_('priority'), default=False, db_index=True)

    country = models.ForeignKey('indigo_api.Country', verbose_name=_('country'), related_name='workflows', null=False, blank=False, on_delete=models.CASCADE)
    locality = models.ForeignKey('indigo_api.Locality', verbose_name=_('locality'), related_name='workflows', null=True, blank=True, on_delete=models.CASCADE)

    created_by_user = models.ForeignKey(User, verbose_name=_('created by user'), related_name='+', null=True, on_delete=models.SET_NULL)
    updated_by_user = models.ForeignKey(User, verbose_name=_('updated by user'), related_name='+', null=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)


    @property
    def place(self):
        return self.locality or self.country

    @property
    def overdue(self):
        return self.due_date and self.due_date < datetime.date.today()

    @property
    def summary(self):
        """ First part of the workflow description before a blank line.
        """
        return (self.description or '').replace('\r\n', '\n').split('\n\n', 1)[0]

    def __str__(self):
        return self.title


@receiver(signals.post_save, sender=Workflow)
def post_save_workflow(sender, instance, **kwargs):
    """ Send 'created' action to activity stream if new workflow
    """
    if kwargs['created']:
        action.send(instance.created_by_user, verb='created', action_object=instance,
                    place_code=instance.place.place_code)


class TaskLabel(models.Model):
    title = models.CharField(_('title'), max_length=30, null=False, unique=True, blank=False)
    slug = models.SlugField(_('slug'), null=False, unique=True, blank=False)
    description = models.CharField(_('description'), max_length=256, null=True, blank=True)

    class Meta:
        ordering = ['title']
        verbose_name = _('task label')
        verbose_name_plural = _('task labels')

    def __str__(self):
        return self.title


def task_file_filename(instance, filename):
    subdirectory = 'input' if hasattr(instance, 'task_as_input') else 'output'
    task_id = instance.task_as_input.id if hasattr(instance, 'task_as_input') else instance.task_as_output.id
    return f'task-file-attachments/{subdirectory}/{task_id}-{filename}'


class TaskFile(models.Model):
    file = models.FileField(_('file'), upload_to=task_file_filename, null=True, blank=True)
    url = models.URLField(_('URL'), null=True, blank=True)
    size = models.IntegerField(_('size'), null=True)
    filename = models.CharField(_('filename'), max_length=1024)
    mime_type = models.CharField(_('mimetype'), max_length=1024)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('task file')
        verbose_name_plural = _('task files')
