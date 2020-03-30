# -*- coding: utf-8 -*-
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
from indigo_api.models import Subtype, Work, PublicationDocument, Task, Amendment, Commencement, VocabularyTopic
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
    stub = forms.BooleanField(required=False)
    # handle spreadsheet that still uses 'principal'
    principal = forms.BooleanField(required=False)
    commenced_by = forms.CharField(required=False)
    amends = forms.CharField(required=False)
    repealed_by = forms.CharField(required=False)
    taxonomy = forms.CharField(required=False)

    def clean_title(self):
        title = self.cleaned_data.get('title')
        return re.sub('[\u2028 ]+', ' ', title)


@plugins.register('bulk-creator')
class BaseBulkCreator(LocaleBasedMatcher):
    """ Create works in bulk from a google sheets spreadsheet.
    Subclass RowValidationFormBase() and get_row_validation_form() to check / raise errors for different fields.
    """
    locale = (None, None, None)
    """ The locale this bulk creator is suited for, as ``(country, language, locality)``.
    """

    aliases = []
    """ list of tuples of the form ('alias', 'meaning')
    (to be declared by subclasses), e.g. ('gazettement_date', 'publication_date')
    """

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
            raise ValidationError("Error talking to Google Sheets: %s" % str(e))

        reader = csv.reader(io.StringIO(response.content.decode('utf-8')))
        rows = list(reader)

        if not rows or not rows[0]:
            raise ValidationError(
                "Your sheet did not import successfully; "
                "please check that you have link sharing ON (Anyone with the link)."
            )
        return rows

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
                raise ValueError(str(e))

        return []

    def get_datatable_gsheets(self, spreadsheet_id, sheet_name):
        """ Fetch a datatable from a Google Sheets spreadsheet, using the given URL and sheet
        index (tab index).
        """
        try:
            result = self.gsheets_client\
                .spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet_name)\
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

    def create_works(self, view, table, dry_run, workflow, user):
        self.workflow = workflow
        self.user = user

        works = []

        # clean up headers
        headers = [h.split(' ')[0].lower() for h in table[0]]

        # Transform rows into list of dicts for easy access.
        # The rows in table only have entries up to the last non-empty cell,
        # so we ensure that we have at least an empty string for every header.
        rows = [
            {header: (row[i] if i < len(row) else '') for i, header in enumerate(headers) if header}
            for row in table[1:]
        ]

        for idx, row in enumerate(rows):
            # ignore if it's blank or explicitly marked 'ignore' in the 'ignore' column
            if row.get('ignore') or not [val for val in row.values() if val]:
                continue

            works.append(self.create_work(view, row, idx, dry_run))

        if not dry_run:
            for info in works:
                if info['status'] == 'success':
                    if info.get('commencement_date') or info.get('commenced_by'):
                        self.link_commencement(info['work'], info)

                    if info.get('repealed_by'):
                        self.link_repeal(info['work'], info)

                    if info.get('primary_work'):
                        self.link_parent_work(info['work'], info)

                    if info.get('taxonomy'):
                        self.link_taxonomy(info['work'], info)

                if info['status'] != 'error' and info.get('amends'):
                    # this will check duplicate works as well
                    # (they won't overwrite the existing works but the amendments will be linked)
                    self.link_amendment(info['work'], info)

        return works

    def create_work(self, view, row, idx, dry_run):
        # copy all row details
        info = row
        info['row'] = idx + 2

        row = self.validate_row(view, row)

        if row.get('errors'):
            info['status'] = 'error'
            info['error_message'] = row['errors']
            return info

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
            work.commenced = bool(row.get('commencement_date') or row.get('commenced_by'))
            work.assent_date = row.get('assent_date')
            work.stub = row.get('stub')
            # handle spreadsheet that still uses 'principal'
            if 'stub' not in info:
                work.stub = not row.get('principal')
            work.created_by_user = view.request.user
            work.updated_by_user = view.request.user
            self.add_extra_properties(work, info)

            try:
                work.full_clean()
                if not dry_run:
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

                    self.link_publication_document(work, info)

                    if not work.stub:
                        self.create_task(work, info, task_type='import')

                info['work'] = work
                info['status'] = 'success'

            except ValidationError as e:
                info['status'] = 'error'
                if hasattr(e, 'message_dict'):
                    info['error_message'] = ' '.join(
                        ['%s: %s' % (f, '; '.join(errs)) for f, errs in e.message_dict.items()]
                    )
                else:
                    info['error_message'] = str(e)

        return info

    def transform_aliases(self, row):
        """ Adds the term the platform expects to `row` for validation (and later saving).
        e.g. if the spreadsheet has `gazettement_date` where we expect `publication_date`,
        `publication_date` and the appropriate value will be added to `row`
        if ('gazettement_date', 'publication_date') was specified in the subclass's aliases
        """
        for alias, meaning in self.aliases:
            if alias in row:
                row[meaning] = row[alias]

    def transform_error_aliases(self, errors):
        """ Changes the term the platform expects back into its alias for displaying.
        e.g. if spreadsheet has `gazettement_date` where we expect `publication_date`,
        the error will display as `gazettement_date`
        if ('gazettement_date', 'publication_date') was specified in the subclass's aliases
        """
        for alias, meaning in self.aliases:
            for title in errors.keys():
                if meaning == title:
                    errors[alias] = errors.pop(title)

    def validate_row(self, view, row):
        row_country = row.get('country')
        row_locality = row.get('locality')
        row_subtype = row.get('subtype')
        self.transform_aliases(row)
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
        self.transform_error_aliases(errors)

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

    def add_extra_properties(self, work, info):
        place = self.locality or self.country
        for extra_property in place.settings.work_properties.keys():
            if info.get(extra_property):
                work.properties[extra_property] = info.get(extra_property)

    def link_publication_document(self, work, info):
        params = info.get('params')
        locality_code = self.locality.code if self.locality else None
        finder = plugins.for_locale('publications', self.country.code, None, locality_code)

        if not finder or not params.get('date'):
            return self.create_task(work, info, task_type='link-publication-document')

        publications = finder.find_publications(params)

        if len(publications) != 1:
            return self.create_task(work, info, task_type='link-publication-document')

        pub_doc_details = publications[0]
        pub_doc = PublicationDocument()
        pub_doc.work = work
        pub_doc.file = None
        pub_doc.trusted_url = pub_doc_details.get('url')
        pub_doc.size = pub_doc_details.get('size')
        pub_doc.save()

    def link_commencement(self, work, info):
        # if the work has commencement details, try linking it
        # make a task if a `commenced_by` title is given but not found
        date = info.get('commencement_date') or None

        commencing_work = None
        title = info.get('commenced_by')
        if title:
            commencing_work = self.find_work_by_title(title)
            if not commencing_work:
                self.create_task(work, info, task_type='link-commencement')

        commencement = Commencement(
            commenced_work=work,
            commencing_work=commencing_work,
            date=date,
            main=True,
            all_provisions=True,
            created_by_user=self.user
        )
        commencement.save()

    def link_repeal(self, work, info):
        # if the work is `repealed_by` something, try linking it
        # make a task if this fails
        # (either because the work isn't found or because the repeal date isn't right,
        # which could be because it doesn't exist or because it's in the wrong format)
        repealing_work = self.find_work_by_title(info['repealed_by'])
        if not repealing_work:
            return self.create_task(work, info, task_type='link-repeal')

        repeal_date = repealing_work.commencement_date
        if not repeal_date:
            return self.create_task(work, info, task_type='link-repeal')

        work.repealed_by = repealing_work
        work.repealed_date = repeal_date

        try:
            work.save_with_revision(self.user)
        except ValidationError:
            self.create_task(work, info, task_type='link-repeal')

    def link_parent_work(self, work, info):
        # if the work has a `primary_work`, try linking it
        # make a task if this fails
        parent_work = self.find_work_by_title(info['primary_work'])
        if not parent_work:
            return self.create_task(work, info, task_type='link-primary-work')

        work.parent_work = parent_work

        try:
            work.save_with_revision(self.user)
        except ValidationError:
            self.create_task(work, info, task_type='link-primary-work')

    def link_amendment(self, work, info):
        # if the work `amends` something, try linking it
        # (this will only work if there's only one amendment listed)
        # make a task if this fails
        amended_work = self.find_work_by_title(info['amends'])
        if not amended_work:
            return self.create_task(work, info, task_type='link-amendment')

        date = info.get('commencement_date') or work.commencement_date
        if not date:
            return self.create_task(work, info, task_type='link-amendment')

        try:
            Amendment.objects.get(
                amended_work=amended_work,
                amending_work=work,
                date=date
            )

        except Amendment.DoesNotExist:
            amendment = Amendment()
            amendment.amended_work = amended_work
            amendment.amending_work = work
            amendment.created_by_user = self.user
            amendment.date = date
            amendment.save()

    def link_taxonomy(self, work, info):
        topics = [x.strip(",") for x in info.get('taxonomy').split()]
        unlinked_topics = []
        for t in topics:
            topic = VocabularyTopic.get_topic(t)
            if topic:
                work.taxonomies.add(topic)
                work.save_with_revision(self.user)

            else:
                unlinked_topics.append(t)
        if unlinked_topics:
            info['unlinked_topics'] = ", ".join(unlinked_topics)
            self.create_task(work, info, task_type='link-taxonomy')

    def create_task(self, work, info, task_type):
        task = Task()

        if task_type == 'link-publication-document':
            task.title = 'Link gazette'
            task.description = '''This work's gazette (original publication document) could not be linked automatically – see row {}.
Find it and upload it manually.'''.format(info['row'])

        elif task_type == 'import':
            task.title = 'Import content'
            task.description = '''Import a point in time for this work; either the initial publication or a later consolidation.
Make sure the document's expression date is correct.'''

        elif task_type == 'link-commencement':
            task.title = 'Link commencement'
            task.description = '''On the spreadsheet, it says that this work is commenced by '{}' – see row {}.

The commencement work could not be linked automatically.
Possible reasons:
– a typo in the spreadsheet
– more than one work by that name exists on the system
– the commencing work doesn't exist on the system.

Check the spreadsheet for reference and link it manually.'''.format(info['commenced_by'], info['row'])

        elif task_type == 'link-amendment':
            task.title = 'Link amendment(s)'
            amended_title = info['amends']
            if len(amended_title) > 256:
                amended_title = "".join(amended_title[:256] + ', etc')
            task.description = '''On the spreadsheet, it says that this work amends '{}' – see row {}.

The amendment could not be linked automatically.
Possible reasons:
– a typo in the spreadsheet
– no date for the amendment
– more than one amended work listed
– the amended work doesn't exist on the system.

Check the spreadsheet for reference and link it/them manually,
or add the 'Pending commencement' label to this task if it doesn't have a date yet.'''.format(amended_title, info['row'])

        elif task_type == 'link-repeal':
            task.title = 'Link repeal'
            task.description = '''On the spreadsheet, it says that this work was repealed by '{}' – see row {}.

The repeal could not be linked automatically.
Possible reasons:
– a typo in the spreadsheet
– no date for the repeal
– more than one work by that name exists on the system
– the repealing work doesn't exist on the system.

Check the spreadsheet for reference and link it manually,
or add the 'Pending commencement' label to this task if it doesn't have a date yet.'''.format(info['repealed_by'], info['row'])

        elif task_type == 'link-primary-work':
            task.title = 'Link primary work'
            task.description = '''On the spreadsheet, it says that this work's primary work is '{}' – see row {}.

The primary work could not be linked automatically.
Possible reasons:
– a typo in the spreadsheet
– more than one work by that name exists on the system
– the primary work doesn't exist on the system.

Check the spreadsheet for reference and link it manually.'''.format(info['primary_work'], info['row'])

        elif task_type == 'link-taxonomy':
            task.title = 'Link taxonomy/ies'
            task.description = '''On the spreadsheet, it says that this work has the following taxonomy/ies: '{}' – see row {}.

The taxonomy/ies work could not be linked automatically.
Possible reasons:
– a typo in the spreadsheet
– the taxonomy/ies doesn't/don't exist on the system.'''.format(info['unlinked_topics'], info['row'])

        task.country = self.country
        task.locality = self.locality
        task.work = work
        task.code = task_type
        task.created_by_user = self.user

        # need to save before assigning workflow because of M2M relation
        task.save()
        if self.workflow:
            task.workflows = [self.workflow]
            task.save()

        return task

    def find_work_by_title(self, title):
        potential_matches = Work.objects.filter(title=title, country=self.country, locality=self.locality)
        if len(potential_matches) == 1:
            return potential_matches.first()

    @property
    def share_with(self):
        if not self._gsheets_secret:
            self._gsheets_secret = settings.INDIGO['GSHEETS_API_CREDS']

        return self._gsheets_secret.get('client_email')
