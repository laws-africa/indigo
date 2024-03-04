from itertools import chain

from django.utils.translation import gettext as _

from indigo_api.models import Task


class TaskBroker:
    def __init__(self, works):
        self.works = works.order_by("-created_at")
        self.import_task_works = works.filter(principal=True)
        self.import_tasks = None
        self.gazette_task_works = [w for w in works if not w.has_publication_document()]
        self.gazette_tasks = None
        all_amendments = [w.amendments.all() for w in works if w.amendments.exists()] + \
                         [w.amendments_made.all() for w in works if w.amendments_made.exists()]
        self.amendments = set(chain(*all_amendments))
        self.amendments_per_work = {w: w.amendments.filter(pk__in=[a.pk for a in self.amendments])
                                    for w in set(a.amended_work for a in self.amendments)}
        self.amendment_tasks = None

    def create_tasks(self, user, data):
        # import tasks
        # stash the import tasks in case we want to do something with them later
        self.import_tasks = [self.get_or_create_task(work=work, task_type='import-content',
                                                     description=data['import_task_description'],
                                                     user=user, timeline_date=self.get_import_timeline_date(work))
                             for work in self.import_task_works]
        if data.get('update_import_tasks'):
            self.block_or_cancel_tasks(self.import_tasks, data['update_import_tasks'], user)

        # gazette tasks
        # stash the gazette tasks in case we want to do something with them later
        self.gazette_tasks = [self.get_or_create_task(work=work, task_type='link-gazette',
                                                      description=data['gazette_task_description'],
                                                      user=user, timeline_date=work.publication_date)
                              for work in self.gazette_task_works]
        if data.get('update_gazette_tasks'):
            self.block_or_cancel_tasks(self.gazette_tasks, data['update_gazette_tasks'], user)

        # amendment tasks
        # stash the amendment tasks in case we want to do something with them later
        self.amendment_tasks = []
        for amendment in self.amendments:
            self.amendment_tasks.append(self.get_or_create_task(
                work=amendment.amended_work, task_type='apply-amendment',
                description=data[f'amendment_task_description_{amendment.pk}'],
                user=user, timeline_date=amendment.date))
        if data.get('update_amendment_tasks'):
            self.block_or_cancel_tasks(self.amendment_tasks, data['update_amendment_tasks'], user)

    def get_import_timeline_date(self, work):
        import_timeline_dates = [work.publication_date] if work.publication_date else []
        import_timeline_dates.extend(c.date for c in work.arbitrary_expression_dates.all())
        return max(import_timeline_dates) if import_timeline_dates else None

    def get_or_create_task(self, work, task_type, description, user, timeline_date=None):
        task = Task.objects.filter(work=work, code=task_type, timeline_date=timeline_date, state__in=Task.OPEN_STATES).first()
        if not task:
            task = Task(country=work.country, locality=work.locality, work=work,
                        code=task_type, timeline_date=timeline_date, created_by_user=user)

        # set these here in case an existing task is being updated
        task.title = dict(Task.MAIN_CODES)[task_type]
        task.description = description
        task.updated_by_user = user
        task.save()

        if task.state == Task.BLOCKED and not task.blocked_by.exists():
            task.unblock(user)

        return task

    def block_or_cancel_tasks(self, tasks, block_or_cancel, user):
        for task in tasks:
            if block_or_cancel == 'block':
                task.block(user)
            elif block_or_cancel == 'cancel':
                task.cancel(user)
