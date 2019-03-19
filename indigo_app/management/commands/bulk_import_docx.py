import os
from datetime import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import transaction

from indigo.plugins import plugins
from indigo_api.models import Document, Language, Work
from indigo_api.serializers import AttachmentSerializer


class Command(BaseCommand):
    help = 'Imports new docx files on existing works at existing points in time. ' \
           'Example: `python manage.py bulk_import_docx  ~/Namibia/namibia.csv ~/Namibia/STATUTES_DOCX`'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str,
                            help='A path to a .csv file, e.g. `~/Namibia/namibia.csv`.'
                                 'The file MUST have the following headings in the first row: '
                                 '- frbr_uri (of existing work) '
                                 '- date (format: 1985-10-17): this is the expression date of the doc '
                                 '  and should be an existing PiT '
                                 '- language: 2-letter code, e.g. `en` for English '
                                 '- filename: the name of the file to be imported from the directory.'
                            )
        parser.add_argument('path', type=str,
                            help='a path to a directory that contains the docx files '
                                 'given in the .csv file under `filename` '
                            )

    def get_user(self):
        waiting = True
        while waiting:
            try:
                result = int(input('Which user are you? Select the number from the list above: '))
                user = User.objects.get(id=result)
            except:
                print('Something went wrong; try again (you must type a number from the list above)')
            else:
                waiting = False
                return user

    def get_file(self, path_to_filename):
        try:
            return open(path_to_filename)
        except IOError as e:
            print('\nFile error: ' + str(e))

    def handle(self, *args, **options):
        for user in User.objects.all().order_by('id'):
            print('{}: {} {}'.format(user.id, user.first_name, user.last_name))
        user = self.get_user()
        csv_file_name = str(options.get('csv_file'))
        path = options.get('path')
        with open(csv_file_name) as csv_file:
            content = csv_file.readlines()
            content = [r.strip() for r in content]
            headers = [h for h in content[0].split(',')]
            rows = [
                {header: row[i] for i, header in enumerate(headers) if header}
                for row in [r.split(',') for r in content[1:]]
            ]
            for row in rows:
                with transaction.atomic():
                    filename = row.get('filename')
                    path_to_filename = os.path.join(path, filename)
                    docx_file = self.get_file(path_to_filename)
                    if docx_file:
                        work = Work.objects.get(frbr_uri=row.get('frbr_uri'))
                        date = datetime.strptime(row.get('date'), '%Y-%m-%d').date()
                        language = Language.objects.get(language_id=row.get('language'))

                        # document already exists in this language at this date
                        if work.document_set.undeleted().filter(expression_date=date, language=language):
                            print('\nA document already exists for {} at {} in {}; delete it before reimporting.'
                                  .format(work.title, date, str(language)))
                            continue

                        # no point in time at this date for this work
                        elif date not in [pit['date'] for pit in work.points_in_time()]:
                            print('\nNo point in time exists for {} at {}; create it before reimporting.'
                                  .format(work, date))

                        document = Document()
                        document.work = work
                        document.expression_date = date
                        document.language = language
                        document.created_by_user = user

                        importer = plugins.for_document('importer', document)

                        # hard-coded for Namibian docxes
                        importer.section_number_position = 'after-title'

                        try:
                            importer.create_from_docx(docx_file, document)
                        except ValueError as e:
                            print("Error during import: %s" % e.message)
                            raise ValidationError(e.message or "error during import")

                        # TODO: get rid of `updated_by_user` as this isn't what's happening here
                        #  (will have to happen on works.ImportDocumentView as well)
                        document.updated_by_user = user
                        document.save()

                        # TODO: create review task on document

                        # TODO: add source file as an attachment
                        #  (will this fix images too?)
                        # this doesn't work because `doc_file` doesn't have a `size`
                        # (or likely another reason -- it expected `upload`)
                        # AttachmentSerializer(context={'document': document}).create({'file': docx_file})
