from django.core.files import File
from django_fsm import has_transition_perm
from itertools import chain

from indigo_api.models import Task, TaskFile


class TaskBroker:
    def __init__(self, works):
        # the works, filtered
        self.works, self.ignored_works = self.get_works_and_ignored_works(works)
        self.import_task_works = self.works.filter(principal=True)
        self.missing_import_date_works = [w for w in self.import_task_works if not w.get_import_date()]
        self.gazette_task_works = [w for w in self.works if not w.has_publication_document()]
        all_amendments = [w.amendments.all() for w in works if w.amendments.exists()] + \
                         [w.amendments_made.all() for w in works if w.amendments_made.exists()]
        self.amendments = sorted(set(chain(*all_amendments)), key=lambda amendment: (amendment.date, amendment.pk))
        self.amendments_per_work = {w: w.amendments.filter(pk__in=[a.pk for a in self.amendments])
                                    for w in set(a.amended_work for a in self.amendments)}
        # the tasks
        self.conversion_tasks = None
        self.import_tasks = None
        self.gazette_tasks = None
        self.amendment_tasks = None
        self.amendment_instruction_tasks = None

    def get_works_and_ignored_works(self, works):
        """ Return (works, ignored_works) from the form data, partitioning on those that can be approved in bulk
        and those that can't.
        By default, all works in progress can be approved. Subclass to introduce approval requirements.
        """

        return works.all().order_by("-created_at"), works.none()

    def create_tasks(self, user, data):
        # conversion tasks
        self.conversion_tasks = [self.get_or_create_task(work=work, task_type='convert-document',
                                                         description=data['conversion_task_description'],
                                                         user=user, timeline_date=work.get_import_date())
                                 for work in self.import_task_works]
        if data.get('update_conversion_tasks'):
            self.block_or_cancel_tasks(self.conversion_tasks, data['update_conversion_tasks'], user)

        # import tasks
        self.import_tasks = [self.get_or_create_task(work=work, task_type='import-content',
                                                     description=data['import_task_description'],
                                                     user=user, timeline_date=work.get_import_date())
                             for work in self.import_task_works]
        if data.get('update_import_tasks'):
            self.block_or_cancel_tasks(self.import_tasks, data['update_import_tasks'], user)

        # update the conversion tasks: optionally create input TaskFiles and block open import tasks
        for task in self.conversion_tasks:
            self.make_input_task_file(task, use_publication_document=task.work.has_publication_document())
            # block (only) the import task we've just created on this work
            import_task = task.work.tasks.get(pk__in=[t.pk for t in self.import_tasks])
            import_task.blocked_by.add(task)
            if import_task.state in Task.UNBLOCKED_STATES:
                import_task.block(user)

        # gazette tasks
        self.gazette_tasks = [self.get_or_create_task(work=work, task_type='link-gazette',
                                                      description=data['gazette_task_description'],
                                                      user=user, timeline_date=work.publication_date)
                              for work in self.gazette_task_works]
        if data.get('update_gazette_tasks'):
            self.block_or_cancel_tasks(self.gazette_tasks, data['update_gazette_tasks'], user)

        # amendment tasks
        self.amendment_tasks = []
        self.amendment_instruction_tasks = []
        for amendment in self.amendments:
            if data.get(f'amendment_task_create_{amendment.pk}'):
                work = amendment.amended_work

                # ensure there is an amendment instruction task, which the apply amendment task will be blocked by.
                instruction_task = self.get_or_create_task(
                    work=work, task_type='amendment-instructions', timeline_date=amendment.date, user=user,
                    description=Task.DESCRIPTIONS['amendment-instructions'],
                )
                self.amendment_instruction_tasks.append(instruction_task)

                # create new amendment tasks so that we don't overwrite descriptions on existing tasks
                amendment_task = Task.objects.create(
                    country=work.country, locality=work.locality, work=work,
                    code='apply-amendment', title=Task.MAIN_CODES['apply-amendment'],
                    timeline_date=amendment.date,
                    description=data[f'amendment_task_description_{amendment.pk}'],
                    created_by_user=user)
                self.amendment_tasks.append(amendment_task)

                # always block the new amendment task by the instruction task
                amendment_task.blocked_by.add(self.amendment_instruction_tasks[-1])

                # block the new amendment task by the most recent open apply-amendment task
                # that already exists before this amendment's timeline date.
                prior_amendment_task = Task.objects.filter(
                    work=work,
                    code='apply-amendment',
                    timeline_date__lt=amendment.date,
                    state__in=Task.OPEN_STATES,
                ).order_by('-timeline_date', '-pk').first()
                if prior_amendment_task:
                    amendment_task.blocked_by.add(prior_amendment_task)

                if not data.get('update_amendment_tasks'):
                    # if update_amendment_tasks has a value, then it will be processed below, otherwise we default
                    # to blocking the amendment task
                    amendment_task.block(user)

        if data.get('update_amendment_tasks'):
            # block or cancel only amendment tasks, since instruction tasks don't need to block on anything
            self.block_or_cancel_tasks(self.amendment_tasks, data['update_amendment_tasks'], user)

    def make_input_task_file(self, task, use_publication_document=False):
        """ Create and link an input TaskFile from the publication document, if there is one """
        if use_publication_document:
            input_file = TaskFile()
            publication_document = task.work.publication_document
            if publication_document.trusted_url:
                input_file.url = publication_document.trusted_url
                self.save_input_file_using_publication_document_info(input_file, task, publication_document)
            elif publication_document.file:
                # make a copy of the publication document's file, since the task form can be edited and the file deleted
                input_file.file = File(publication_document.file, name=publication_document.filename)
                self.save_input_file_using_publication_document_info(input_file, task, publication_document)
            task.input_file = input_file
            task.save()

    def save_input_file_using_publication_document_info(self, input_file, task, publication_document):
        input_file.filename = publication_document.filename
        input_file.mime_type = publication_document.mime_type
        input_file.size = publication_document.size
        input_file.task_as_input = task
        input_file.save()

    def get_or_create_task(self, work, task_type, description, user, timeline_date=None):
        task = Task.objects.filter(work=work, code=task_type, timeline_date=timeline_date, state__in=Task.OPEN_STATES).first()
        if not task:
            task = Task(country=work.country, locality=work.locality, work=work,
                        code=task_type, timeline_date=timeline_date, created_by_user=user)

        # set these here in case an existing task is being updated
        task.title = Task.MAIN_CODES[task_type]
        task.description = description
        task.updated_by_user = user
        task.save()

        if task.state == Task.BLOCKED and not task.blocked_by.exists():
            task.unblock(user)

        return task

    def block_or_cancel_tasks(self, tasks, block_or_cancel, user):
        for task in tasks:
            if block_or_cancel == 'block' and has_transition_perm(task.block, user):
                task.block(user)
            elif block_or_cancel == 'cancel' and has_transition_perm(task.cancel, user):
                task.cancel(user)
