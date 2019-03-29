from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from indigo.plugins import plugins
from indigo_api.models import Country, PublicationDocument, Task, Work


class Command(BaseCommand):
    help = 'links publication documents if they\'re available through Gazette Machine per country' \
           'Example: `python manage.py backfill_publication_docs na'

    def add_arguments(self, parser):
        parser.add_argument('country_code', type=str, help='A two-letter country code, e.g. \'na\' for Namibia')

    def get_country(self, country_code):
        return Country.objects.get(country_id=country_code.upper())

    def get_works(self, country):
        return Work.objects.get(country=country)

    def get_params(self, work):
        params = {
            # TODO: make pub_date into a literal?
            'date': work.publication_date,
            'number': work.publication_number,
            'publication': work.publication_name,
            'country': work.country.place_code,
            'locality': work.locality.code if work.locality else None,
        }
        return params

    def pub_doc_task(self, work, task_type):
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

            task.country = work.country
            task.locality = work.locality
            task.work = work
            task.created_by_user = self.request.user
            task.save()

            # TODO create new workflow just for these and add them to it
            # task.workflows = form.cleaned_data.get('workflows').all()
            # task.save()

    def get_publication_document(self, params, work):
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
                    self.pub_doc_task(work, task_type='check')

                else:
                    self.pub_doc_task(work, task_type='link')

            except ValueError as e:
                raise ValidationError({'message': e.message})

        else:
            self.pub_doc_task(work, task_type='link')

    def handle(self, *args, **options):
        country = self.get_country(options.get('country_code'))
        works = self.get_works(country)
        for work in works:
            params = self.get_params(work)
            self.get_publication_document(params, work)
