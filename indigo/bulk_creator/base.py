# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals

import datetime
import re

from cobalt import FrbrUri
from django.core.exceptions import ValidationError

from indigo.plugins import LocaleBasedMatcher, plugins
from indigo_api.models import Work
from indigo_api.signals import work_changed


@plugins.register('bulk-creator')
class BaseBulkCreator(LocaleBasedMatcher):
    """ Create works in bulk from a google sheets spreadsheet.
    Overwrite get_frbr_uri() to check / raise errors for different fields.
    """
    locale = (None, None, None)
    """ The locale this bulk creator is suited for, as ``(country, language, locality)``.
    """

    def get_works(self, view, table):
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

                        # signals
                        work_changed.send(sender=work.__class__, work=work, request=view.request)

                        # info for links
                        pub_doc_params = {
                            'date': row.get('publication_date'),
                            'number': work.publication_number,
                            'publication': work.publication_name,
                            'country': view.country.place_code,
                            'locality': view.locality.code if view.locality else None,
                        }
                        info['params'] = pub_doc_params

                        work_links = ['commenced_by', 'amends', 'repealed_by', 'primary_work']
                        for link in work_links:
                            info[link] = row.get(link)

                        info['status'] = 'success'
                        info['work'] = work

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
        frbr_uri = FrbrUri(country=row_country,
                           locality=row_locality,
                           doctype='act',
                           subtype=row.get('subtype'),
                           date=row.get('year'),
                           number=row.get('number'),
                           actor=None)

        # if the country doesn't match
        # (but ignore if no country given – dealt with separately)
        if row_country and country.code != row_country.lower():
            raise ValueError(
                'The country code given in the spreadsheet ("%s") '
                'doesn\'t match the code for the country you\'re working in ("%s")'
                % (row_country, country.code.upper())
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
