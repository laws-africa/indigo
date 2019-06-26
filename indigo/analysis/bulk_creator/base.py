# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals

import datetime
import re

from cobalt import FrbrUri
from django.core.exceptions import ValidationError

from indigo.plugins import LocaleBasedMatcher, plugins
from indigo_api.models import Work, Task, PublicationDocument
from indigo_api.signals import work_changed


class BaseBulkCreator(LocaleBasedMatcher):
    """ Create works in bulk from a google sheets spreadsheet.
    """
    def get_works(self, view, table, form):
        works = []

        # clean up headers
        headers = [h.split(' ')[0].lower() for h in table[0]]

        # transform rows into list of dicts for easy access
        rows = [
            {header: row[i] for i, header in enumerate(headers) if header}
            for row in table[1:]
        ]

        for idx, row in enumerate(rows):
            # ignore if it's blank or explicitly marked 'ignore' in the 'ignore' column
            if not row.get('ignore') and [val for val in row.itervalues() if val]:
                info = {
                    'row': idx + 2,
                }
                works.append(info)

                try:
                    frbr_uri = self.get_frbr_uri(view.country, view.locality, row)
                except ValueError as e:
                    info['status'] = 'error'
                    info['error_message'] = e.message
                    continue

                try:
                    work = Work.objects.get(frbr_uri=frbr_uri)
                    info['work'] = work
                    info['status'] = 'duplicate'
                    info['amends'] = row.get('amends') or None
                    info['commencement_date'] = row.get('commencement_date') or None

                except Work.DoesNotExist:
                    work = Work()

                    work.frbr_uri = frbr_uri
                    work.title = self.strip_title_string(row.get('title'))
                    work.country = view.country
                    work.locality = view.locality
                    work.publication_name = row.get('publication_name')
                    work.publication_number = row.get('publication_number')
                    work.created_by_user = view.request.user
                    work.updated_by_user = view.request.user
                    work.stub = not row.get('principal')
                    work.publication_date = self.make_date(row.get('publication_date'), 'publication_date') or None
                    work.commencement_date = self.make_date(row.get('commencement_date'), 'commencement_date') or None
                    work.assent_date = self.make_date(row.get('assent_date'), 'assent_date') or None

                    try:
                        work.full_clean()
                        work.save_with_revision(view.request.user)

                        # link publication document
                        publication_number = work.publication_number.split()[-1]
                        params = {
                            'date': row.get('publication_date'),
                            'number': publication_number,
                            'publication': work.publication_name,
                            'country': view.country.place_code,
                            'locality': view.locality.code if view.locality else None,
                        }
                        self.get_publication_document(params, work, form, view.request.user)

                        # signals
                        work_changed.send(sender=work.__class__, work=work, request=view.request)

                        info['status'] = 'success'
                        info['work'] = work

                        # TODO: neaten this up
                        if row.get('commenced_by'):
                            info['commenced_by'] = row.get('commenced_by')
                        if row.get('amends'):
                            info['amends'] = row.get('amends')
                        if row.get('repealed_by'):
                            info['repealed_by'] = row.get('repealed_by')
                        if row.get('primary_work'):
                            info['parent_work'] = row.get('primary_work')

                    except ValidationError as e:
                        info['status'] = 'error'
                        if hasattr(e, 'message_dict'):
                            info['error_message'] = ' '.join(
                                ['%s: %s' % (f, '; '.join(errs)) for f, errs in e.message_dict.items()]
                            )
                        else:
                            info['error_message'] = e.message

        return works

    def get_frbr_uri(self, country, locality, row):
        row_country = row.get('country')
        row_locality = row.get('locality')
        row_subtype = row.get('subtype')
        row_year = row.get('year')
        row_number = row.get('number')
        frbr_uri = FrbrUri(country=row_country, locality=row_locality,
                           doctype='act', subtype=row_subtype,
                           date=row_year, number=row_number, actor=None)

        # if the country doesn't match
        # (but ignore if no country given – dealt with separately)
        if row_country and country.code != row_country.lower():
            raise ValueError(
                'The country code given in the spreadsheet ("%s") '
                'doesn\'t match the code for the country you\'re working in ("%s")'
                % (row.get('country'), country.code.upper())
            )

        # if you're working on the country level but the spreadsheet gives a locality
        if not locality and row_locality:
            raise ValueError(
                'You are working in a country (%s), '
                'but the spreadsheet gives a locality code ("%s")'
                % (country, row_locality)
            )

        # if you're working in a locality but the spreadsheet doesn't give one
        if locality and not row_locality:
            raise ValueError(
                'There\'s no locality code given in the spreadsheet, '
                'but you\'re working in %s ("%s")'
                % (locality, locality.code.upper())
            )

        # if the locality doesn't match
        # (only if you're in a locality)
        if locality and locality.code != row_locality.lower():
            raise ValueError(
                'The locality code given in the spreadsheet ("%s") '
                'doesn\'t match the code for the locality you\'re working in ("%s")'
                % (row_locality, locality.code.upper())
            )

        # check all frbr uri fields have been filled in and that no spaces were accidentally included
        if ' ' in frbr_uri.work_uri():
            raise ValueError('Check for spaces in country, locality, subtype, year, number – none allowed')
        elif not frbr_uri.country:
            raise ValueError('A country must be given')
        elif not frbr_uri.date:
            raise ValueError('A year must be given')
        elif not frbr_uri.number:
            raise ValueError('A number must be given')

        # check that necessary work fields have been filled in
        elif not row.get('title'):
            raise ValueError('A title must be given')
        elif not row.get('publication_date'):
            raise ValueError('A publication date must be given')

        return frbr_uri.work_uri().lower()

    def make_date(self, string, field):
        if not string:
            date = None
        else:
            try:
                date = datetime.datetime.strptime(string, '%Y-%m-%d')
            except ValueError:
                raise ValidationError('Check the format of %s; it should be e.g. "2012-12-31"' % field)
        return date

    def strip_title_string(self, title_string):
        return re.sub(u'[\u2028 ]+', ' ', title_string)

    def get_publication_document(self, params, work, form, user):
        finder = plugins.for_locale('publications', params['country'], None, params['locality'])

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

                else:
                    self.pub_doc_task(work, form, user)

            except ValueError as e:
                raise ValidationError({'message': e.message})

        else:
            self.pub_doc_task(work, form, user)

    def pub_doc_task(self, work, form, user):
        task = Task()

        task.title = 'Link publication document'
        task.description = '''This work's publication document could not be linked automatically.
There may be more than one candidate, or it may be unavailable.
First check under 'Edit work' for multiple candidates. If there are, choose the correct one.
Otherwise, find it and upload it manually.'''

        task.country = work.country
        task.locality = work.locality
        task.work = work
        task.created_by_user = user
        task.save()
        task.workflows = form.cleaned_data.get('workflows').all()
        task.save()

