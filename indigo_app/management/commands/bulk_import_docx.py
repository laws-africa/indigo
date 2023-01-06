import csv
import os
from datetime import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.core.management.base import BaseCommand
from django.db import transaction

from indigo.plugins import plugins
from indigo_api.models import Attachment, Document, Language, Task, Work


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
                                 '- language: 3-letter code, e.g. `eng` for English '
                                 '- filename: the name of the docx file to be imported from the directory.'
                            )
        parser.add_argument('path', type=str,
                            help='a path to a directory that contains the docx files '
                                 'given in the .csv file under `filename` '
                            )

    def get_user(self):
        for user in User.objects.all().order_by('id'):
            print('{}: {} {}'.format(user.id, user.first_name, user.last_name))
        while True:
            try:
                result = int(eval(input('Which user are you? Select the number from the list above: ')))
                user = User.objects.get(id=result)
            except:
                print('\nSomething went wrong; try again (you must type a number from the list above)\n\n')
            else:
                print('\nUser selected: {} {}.\n\n'.format(user.first_name, user.last_name))
                return user

    def get_file(self, i, path_to_filename):
        try:
            return open(path_to_filename)
        except IOError as e:
            print('\nERROR at row {}:'.format(i + 2))
            print('File error: ' + str(e) + '\n')

    def import_rows(self, user, csv_file, path):
        content = csv.DictReader(csv_file)
        for i, row in enumerate(content):
            with transaction.atomic():
                filename = row.get('filename')
                path_to_filename = os.path.join(path, filename)
                docx_file = self.get_file(i, path_to_filename)
                if docx_file:
                    work = Work.objects.get(frbr_uri=row.get('frbr_uri'))
                    date = datetime.strptime(row.get('date'), '%Y-%m-%d').date()
                    language = Language.objects.get(language__iso_639_3=row.get('language'))

                    # document already exists in this language at this date
                    if work.document_set.undeleted().filter(expression_date=date, language=language):
                        print('\nERROR at row {}:'.format(i + 2))
                        print('A document already exists for {} at {} in {}; delete it before reimporting.\n'
                              .format(work.title, date, str(language)))
                        continue

                    # no point in time at this date for this work
                    elif date not in [pit['date'] for pit in work.possible_expression_dates()]:
                        print('\nERROR at row {}:'.format(i + 2))
                        print('No point in time exists for {} at {}; create it before reimporting.\n'
                              .format(work, date))
                        continue

                    filesize = os.path.getsize(path_to_filename)

                    self.import_docx_file(user, work, date, language, docx_file, filesize)

    def create_review_task(self, document, user, filename):
        task = Task()
        task.title = 'Review batch-imported document'
        task.description = '''
        This document was imported as part of a batch from the file '{}'.
        - Double-check that the content is on the right work and at the right point in time.
        - Clean up any import errors as with a normal import.
        '''.format(filename)
        task.country = document.work.country
        task.locality = document.work.locality
        task.work = document.work
        task.document = document
        task.created_by_user = user
        task.save()

    def import_docx_file(self, user, work, date, language, docx_file, filesize):
        document = Document()
        document.work = work
        document.expression_date = date
        document.language = language
        document.created_by_user = user
        document.save()

        importer = plugins.for_document('importer', document)

        # hard-coded for Namibian docxes
        importer.section_number_position = 'after-title'
        upload = UploadedFile(file=docx_file,
                              content_type=DOCX_MIME_TYPE,
                              size=filesize)

        try:
            importer.create_from_upload(upload, document, None)
        except ValueError as e:
            print("Error during import: %s" % str(e))
            raise ValidationError(str(e) or "error during import")

        docx_file.seek(0)
        filename = os.path.split(docx_file.name)[1]

        att = Attachment()
        att.filename = filename
        att.mime_type = DOCX_MIME_TYPE
        att.document = document
        att.size = filesize
        att.file.save(att.filename, docx_file)

        document.updated_by_user = user
        document.save_with_revision(user)
        self.create_review_task(document, user, filename)

        # TODO: fix action signal to be `created` rather than `updated`

    def handle(self, *args, **options):
        user = self.get_user()
        csv_file_name = str(options.get('csv_file'))
        path = options.get('path')
        with open(csv_file_name) as csv_file:
            self.import_rows(user, csv_file, path)
