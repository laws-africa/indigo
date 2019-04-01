from __future__ import unicode_literals

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

    def get_user(self):
        for user in User.objects.all().order_by('id'):
            print('{}: {} {}'.format(user.id, user.first_name, user.last_name))
        while True:
            try:
                result = int(input('Which user are you? Select the number from the list above: '))
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
            # TODO: Python 3 doesn't have `unicode()`
            'date': unicode(work.publication_date),
            'number': work.publication_number,
            'publication': work.publication_name,
            'country': work.country.place_code,
            'locality': work.locality.code if work.locality else None,
        }
        return params

    def pub_doc_task(self, work, user, task_type):
        task = Task()

        if task_type == 'link':
            task.title = 'Link publication document'
            task.description = '''This work's publication document could not be linked automatically.
There may be more than one candidate, or it may be unavailable.
First check under 'Edit work' for multiple candidates. If there are, choose the correct one.
Otherwise, find it and upload it manually.'''

        elif task_type == 'check':
            task.title = 'Check publication document'
            task.description = '''This work's publication document was linked automatically.
Double-check that it's the right one.'''
            task.state = 'pending_review'

        task.country = work.country
        task.locality = work.locality
        task.work = work
        task.created_by_user = user
        task.save()

        workflow_review_title = 'Review automatically linked publication documents'
        try:
            workflow = Workflow.objects.get(title=workflow_review_title)

        except Workflow.DoesNotExist:
            workflow = Workflow()
            workflow.title = workflow_review_title
            workflow.description = '''These publication documents were automatically linked.
Some may have been unsuccessful, and need to be done manually.
The rest need to be checked for accuracy.'''
            workflow.country = task.country
            workflow.locality = task.locality
            workflow.created_by_user = user
            workflow.save()

        workflow.tasks.add(task)
        workflow.updated_by_user = user
        workflow.save()

    def get_publication_document(self, params, work, user):
        finder = plugins.for_locale('publications', work.country, None, work.locality)

        if finder:
            try:
                publications = finder.find_publications(params)

                if len(publications) == 1:
                    pub_doc_details = publications[0]
                    pub_doc = PublicationDocument()
                    pub_doc.work = work
                    pub_doc.file = None
                    pub_doc.trusted_url = pub_doc_details.get('url')
                    pub_doc.size = pub_doc_details.get('size')
                    pub_doc.save()
                    self.pub_doc_task(work, user, task_type='check')

                else:
                    self.pub_doc_task(work, user, task_type='link')

            except ValueError as e:
                raise ValidationError({'message': e.message})

        else:
            self.pub_doc_task(work, user, task_type='link')

    def handle(self, *args, **options):
        user = self.get_user()
        country = self.get_country(options.get('country_code'))
        works_without_pubdocs = self.get_works(country)
        for work in works_without_pubdocs:
            params = self.get_params(work)
            self.get_publication_document(params, work, user)
