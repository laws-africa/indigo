# coding=utf-8
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from indigo.plugins import plugins
from indigo_api.models import Country, PublicationDocument, Task, Work, Workflow


class Command(BaseCommand):
    help = 'links publication documents if they\'re available through Gazette Machine per country' \
           'Example: `python manage.py backfill_publication_docs na'

    def add_arguments(self, parser):
        parser.add_argument('country_code', type=str, help='A two-letter country code, e.g. \'na\' for Namibia')
        parser.add_argument('--dry-run', action='store_true')

    def get_user(self):
        for user in User.objects.all().order_by('id'):
            print('{}: {} – {} {}'.format(user.id, user.username, user.first_name, user.last_name))
        while True:
            try:
                result = int(eval(input('Which user are you? Select the number from the list above: ')))
                user = User.objects.get(id=result)
            except:
                print('\nSomething went wrong; try again (you must type a number from the list above)\n\n')
            else:
                print('\nUser selected: {} {}.\n\n'.format(user.first_name, user.last_name))
                return user

    def get_country(self, country_code):
        return Country.objects.get(country_id=country_code.upper())

    def get_works(self, country):
        return Work.objects.filter(country=country, publication_document=None)

    def get_params(self, work):
        params = {
            'date': str(work.publication_date),
            'number': work.publication_number,
            'publication': work.publication_name,
            'country': work.country.place_code,
            'locality': work.locality.code if work.locality else None,
        }
        return params

    def pub_doc_task(self, work, user):
        task_title = 'Link publication document'

        try:
            Task.objects.get(title=task_title, work=work, state__in=Task.OPEN_STATES + ('cancelled',))

        except Task.DoesNotExist:
            task = Task()

            self.stdout.write(self.style.NOTICE("Creating 'Link publication document' task for {}".format(work)))

            task.title = task_title
            task.description = '''This work's publication document could not be linked automatically.
There may be more than one candidate, or it may be unavailable.
First check under 'Edit work' for multiple candidates. If there are, choose the correct one.
Otherwise, find it and upload it manually.'''

            task.country = work.country
            task.locality = work.locality
            task.work = work
            task.created_by_user = user
            if not self.dry_run:
                task.save()

            workflow_review_title = 'Link publication documents'
            try:
                workflow = work.place.workflows.get(title=workflow_review_title, closed=False)

            except Workflow.DoesNotExist:
                self.stdout.write(self.style.NOTICE("Creating workflow for {}".format(work)))

                workflow = Workflow()
                workflow.title = workflow_review_title
                workflow.description = 'These works\' publication documents could not be automatically linked.'
                workflow.country = task.country
                workflow.locality = task.locality
                workflow.created_by_user = user
                if not self.dry_run:
                    workflow.save()

            if not self.dry_run:
                workflow.tasks.add(task)
                workflow.updated_by_user = user
                workflow.save()

    def get_publication_document(self, params, work, user):
        finder = plugins.for_work('publications', work)

        if finder:
            try:
                publications = finder.find_publications(params)

                if len(publications) == 1:
                    pub_doc_details = publications[0]
                    self.stdout.write(self.style.NOTICE("Linking publication document {} to {}".format(pub_doc_details.get('url'), work)))

                    pub_doc = PublicationDocument()
                    pub_doc.work = work
                    pub_doc.file = None
                    pub_doc.trusted_url = pub_doc_details.get('url')
                    pub_doc.size = pub_doc_details.get('size')
                    if not self.dry_run:
                        pub_doc.save()

                else:
                    self.pub_doc_task(work, user)

            except ValueError as e:
                raise ValidationError({'message': str(e)})

        else:
            self.pub_doc_task(work, user)

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        if self.dry_run:
            self.stdout.write(self.style.NOTICE('Dry-run, won\'t actually make changes'))

        user = self.get_user()
        country = self.get_country(options.get('country_code'))
        works_without_pubdocs = self.get_works(country)

        for work in works_without_pubdocs:
            params = self.get_params(work)
            self.get_publication_document(params, work, user)
