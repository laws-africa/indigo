from itertools import chain

from django.utils.translation import gettext as _

from indigo_api.models import Task


class TaskBroker:
    def __init__(self, works):
        self.works = works.order_by("-created_at")
        self.import_task_works = works.filter(principal=True)
        self.gazette_task_works = [w for w in works if not w.has_publication_document()]
        all_amendments = [w.amendments.all() for w in works if w.amendments.exists()] + \
                         [w.amendments_made.all() for w in works if w.amendments_made.exists()]
        self.amendments = set(chain(*all_amendments))
        self.amendments_per_work = {w: w.amendments.filter(pk__in=[a.pk for a in self.amendments])
                                    for w in set(a.amended_work for a in self.amendments)}

    def create_tasks(self, user, data):
        # import tasks
        # TODO: add the appropriate timeline date for Import tasks too?
        import_tasks = [self.get_or_create_task(work=work, task_type='import-content',
                                                description=data['import_task_description'],
                                                user=user) for work in self.import_task_works]
        if data.get('update_import_tasks'):
            self.block_or_cancel_tasks(import_tasks, data['update_import_tasks'], user)

        # gazette tasks
        gazette_tasks = [self.get_or_create_task(work=work, task_type='link-gazette',
                                                 description=data['gazette_task_description'],
                                                 user=user) for work in self.gazette_task_works]
        if data.get('update_gazette_tasks'):
            self.block_or_cancel_tasks(gazette_tasks, data['update_gazette_tasks'], user)

        # amendment tasks
        amendment_tasks = []
        for amendment in self.amendments:
            amendment_tasks.append(self.get_or_create_task(
                work=amendment.amended_work, task_type='apply-amendment',
                description=data[f'amendment_task_description_{amendment.pk}'],
                user=user, timeline_date=amendment.date))
        if data.get('update_amendment_tasks'):
            self.block_or_cancel_tasks(amendment_tasks, data['update_amendment_tasks'], user)

    def get_or_create_task(self, work, task_type, description, user, timeline_date=None):
        task_titles = {
            'import-content': _('Import content'),
            'link-gazette': _('Link Gazette'),
            'apply-amendment': _('Apply amendment'),
        }
        task_title = task_titles[task_type]

        task = Task.objects.filter(work=work, code=task_type, timeline_date=timeline_date).first()
        if not task:
            task = Task(country=work.country, locality=work.locality, work=work,
                        code=task_type, timeline_date=timeline_date, created_by_user=user)

        task.title = task_title
        task.description = description
        task.updated_by_user = user
        task.save()

        # reopen or unblock tasks: they'll be blocked or cancelled again if needed as chosen in the form
        # TODO: only leave closed tasks as done if they should be:
        #  Gazette tasks never (we've already checked),
        #  Import / Amendment tasks only if there's a published document at the timeline date
        if task.state == Task.CANCELLED:
            task.reopen(user)
        elif task.state == Task.BLOCKED and not task.blocked_by.exists():
            task.unblock(user)

        return task

    def block_or_cancel_tasks(self, tasks, block_or_cancel, user):
        for task in tasks:
            if block_or_cancel == 'block':
                task.block(user)
            elif block_or_cancel == 'cancel':
                task.cancel(user)
