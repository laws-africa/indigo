# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import re
import csv
import io
import logging

from cobalt import FrbrUri
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.conf import settings
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

from indigo.plugins import LocaleBasedMatcher, plugins
from indigo_api.models import Subtype, Work
from indigo_api.signals import work_changed


class RowValidationFormBase(forms.Form):
    country = forms.CharField()
    locality = forms.CharField(required=False)
    title = forms.CharField()
    primary_work = forms.CharField(required=False)
    subtype = forms.CharField(required=False, validators=[
        RegexValidator(r'^\S+$', 'No spaces allowed.')
    ])
    number = forms.CharField(validators=[
        RegexValidator(r'^[a-zA-Z0-9-]+$', 'No spaces or punctuation allowed (use \'-\' for spaces).')
    ])
    year = forms.CharField(validators=[
        RegexValidator(r'\d{4}', 'Must be a year (yyyy).')
    ])
    publication_name = forms.CharField(required=False)
    publication_number = forms.CharField(required=False)
    publication_date = forms.DateField(error_messages={'invalid': 'Date format should be yyyy-mm-dd.'})
    assent_date = forms.DateField(required=False, error_messages={'invalid': 'Date format should be yyyy-mm-dd.'})
    commencement_date = forms.DateField(required=False, error_messages={'invalid': 'Date format should be yyyy-mm-dd.'})
    principal = forms.BooleanField(required=False)
    commenced_by = forms.CharField(required=False)
    amends = forms.CharField(required=False)
    repealed_by = forms.CharField(required=False)

    def clean_title(self):
        title = self.cleaned_data.get('title')
        return re.sub(u'[\u2028 ]+', ' ', title)


@plugins.register('bulk-creator')
class BaseBulkCreator(LocaleBasedMatcher):
    """ Create works in bulk from a google sheets spreadsheet.
    Subclass RowValidationFormBase() and get_row_validation_form() to check / raise errors for different fields.
    """
    locale = (None, None, None)
    """ The locale this bulk creator is suited for, as ``(country, language, locality)``.
    """
    extra_properties = {}

    log = logging.getLogger(__name__)

    _service = None
    _gsheets_secret = None

    GSHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    def gsheets_id_from_url(self, url):
        match = re.match(r'^https://docs.google.com/spreadsheets/d/(\S+)/', url)
        if match:
            return match.group(1)

    def get_datatable(self, spreadsheet_url, sheet_name):
        spreadsheet_id = self.gsheets_id_from_url(spreadsheet_url)
        if not spreadsheet_id:
            raise ValidationError("Unable to extract key from Google Sheets URL")

        if self.is_gsheets_enabled:
            return self.get_datatable_gsheets(spreadsheet_id, sheet_name)
        else:
            return self.get_datatable_csv(spreadsheet_id)

    def get_datatable_csv(self, spreadsheet_id):
        try:
            url = 'https://docs.google.com/spreadsheets/d/%s/export?format=csv' % spreadsheet_id
            response = requests.get(url, timeout=5)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ValidationError("Error talking to Google Sheets: %s" % e.message)

        reader = csv.reader(io.BytesIO(response.content))
        rows = list(reader)

        if not rows or not rows[0]:
            raise ValidationError(
                "Your sheet did not import successfully; "
                "please check that you have link sharing ON (Anyone with the link)."
            )
        return [[item.decode('utf8') for item in row] for row in rows]

    @property
    def is_gsheets_enabled(self):
        return bool(settings.INDIGO.get('GSHEETS_API_CREDS'))

    def get_spreadsheet_sheets(self, spreadsheet_id):
        if self.is_gsheets_enabled:
            try:
                metadata = self.gsheets_client.spreadsheets()\
                    .get(spreadsheetId=spreadsheet_id)\
                    .execute()
                return metadata['sheets']
            except HttpError as e:
                self.log.warning("Error getting data from google sheets for {}".format(spreadsheet_id), exc_info=e)
                raise ValueError(e.message)

        return []

    def get_datatable_gsheets(self, spreadsheet_id, sheet_name):
        """ Fetch a datatable from a Google Sheets spreadsheet, using the given URL and sheet
        index (tab index).
        """
        try:
            result = self.gsheets_client\
                .spreadsheets()\
                .values().get(spreadsheetId=spreadsheet_id, range=sheet_name)\
                .execute()
        except HttpError as e:
            self.log.warning("Error getting data from google sheets for {}".format(spreadsheet_id), exc_info=e)
            raise ValidationError("Unable to access spreadsheet. Is the URL correct and have you shared it with {}?".format(
                self._gsheets_secret['client_email'],
            ))

        rows = result.get('values', [])
        if not rows or not rows[0]:
            raise ValidationError("There doesn't appear to be data in sheet {} of {}".format(sheet_name, spreadsheet_id))
        return rows

    @property
    def gsheets_client(self):
        if not self._service:
            if not self._gsheets_secret:
                self._gsheets_secret = settings.INDIGO['GSHEETS_API_CREDS']
            credentials = service_account.Credentials.from_service_account_info(self._gsheets_secret, scopes=self.GSHEETS_SCOPES)
            self._service = build('sheets', 'v4', credentials=credentials)
        return self._service

    def get_row_validation_form(self, row_data):
        return RowValidationFormBase(row_data)

    def get_works(self, view, table, dry_run):
        works = []

        # clean up headers
        headers = [h.split(' ')[0].lower() for h in table[0]]

        # transform rows into list of dicts for easy access
        rows = [
            {header: row[i] for i, header in enumerate(headers) if header and i < len(row)}
            for row in table[1:]
        ]

        for idx, row in enumerate(rows):
            # ignore if it's blank or explicitly marked 'ignore' in the 'ignore' column
            if row.get('ignore') or not [val for val in row.values() if val]:
                continue

            info = {
                'row': idx + 2,
            }
            works.append(info)

            row = self.validate_row(view, row)

            if row.get('errors'):
                info['status'] = 'error'
                info['error_message'] = row['errors']
                continue

            frbr_uri = self.get_frbr_uri(row)

            try:
                work = Work.objects.get(frbr_uri=frbr_uri)
                info['work'] = work
                info['status'] = 'duplicate'
                info['amends'] = row.get('amends') or None
                info['commencement_date'] = row.get('commencement_date') or None

            except Work.DoesNotExist:
                work = Work()

                work.frbr_uri = frbr_uri
                work.country = view.country
                work.locality = view.locality
                work.title = row.get('title')
                work.publication_name = row.get('publication_name')
                work.publication_number = row.get('publication_number')
                work.publication_date = row.get('publication_date')
                work.commencement_date = row.get('commencement_date')
                work.assent_date = row.get('assent_date')
                work.stub = not row.get('principal')
                work.created_by_user = view.request.user
                work.updated_by_user = view.request.user

                try:
                    work.full_clean()
                    if not dry_run:
                        work.save_with_revision(view.request.user)

                        # signals
                        work_changed.send(sender=work.__class__, work=work, request=view.request)

                        # info for links, extra properties
                        pub_doc_params = {
                            'date': row.get('publication_date'),
                            'number': work.publication_number,
                            'publication': work.publication_name,
                            'country': view.country.place_code,
                            'locality': view.locality.code if view.locality else None,
                        }
                        info['params'] = pub_doc_params

                        for header in headers:
                            info[header] = row.get(header)

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

    def validate_row(self, view, row):
        row_country = row.get('country')
        row_locality = row.get('locality')
        row_subtype = row.get('subtype')
        available_subtypes = [s.abbreviation for s in Subtype.objects.all()]

        row_data = row
        row_data['country'] = view.country.code
        row_data['locality'] = view.locality.code if view.locality else None
        form = self.get_row_validation_form(row_data)

        # Extra validation
        # - if the subtype hasn't been registered
        if row_subtype and row_subtype.lower() not in available_subtypes:
            form.add_error('subtype', 'The subtype given ({}) doesn\'t match any in the list: {}.'
                           .format(row.get('subtype'), ", ".join(available_subtypes)))

        # - if the country is missing or doesn't match
        if not row_country or view.country.code != row_country.lower():
            form.add_error('country', 'The country code given in the spreadsheet ({}) '
                                      'doesn\'t match the code for the country you\'re working in ({}).'
                                      .format(row_country or 'Missing', view.country.code.upper()))

        # - if you're working on the country level but the spreadsheet gives a locality
        #   or the locality doesn't match
        if row_locality:
            if not view.locality:
                form.add_error('locality', 'The spreadsheet gives a locality code ({}), '
                                           'but you\'re working in a country ({}).'
                                           .format(row_locality, view.country.code.upper()))

            elif not view.locality.code == row_locality.lower():
                form.add_error('locality', 'The locality code given in the spreadsheet ({}) '
                                           'doesn\'t match the code for the locality you\'re working in ({}).'
                                           .format(row_locality, view.locality.code.upper()))

        # - if you're working on the locality level but the spreadsheet doesn't give one
        if not row_locality and view.locality:
            form.add_error('locality', 'The spreadsheet doesn\'t give a locality code, '
                                       'but you\'re working in {} ({}).'
                                       .format(view.locality, view.locality.code.upper()))

        errors = form.errors
        row = form.cleaned_data
        row['errors'] = errors
        return row

    def get_frbr_uri(self, row):
        frbr_uri = FrbrUri(country=row.get('country'),
                           locality=row.get('locality'),
                           doctype='act',
                           subtype=row.get('subtype'),
                           date=row.get('year'),
                           number=row.get('number'),
                           actor=None)

        return frbr_uri.work_uri().lower()
