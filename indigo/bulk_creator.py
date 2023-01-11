import datetime
import re
import csv
import io
import logging

from cobalt import FrbrUri
from django import forms
from django.utils.translation import gettext_lazy as __, gettext as _
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.conf import settings
import requests
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

from indigo.plugins import LocaleBasedMatcher, plugins
from indigo_api.models import Subtype, Work, PublicationDocument, Task, Amendment, Commencement, \
    VocabularyTopic, TaskLabel
from indigo_api.signals import work_changed


class SpreadsheetRow:
    def __init__(self, data, errors):
        self.errors = errors
        self.notes = []
        self.relationships = []
        self.tasks = []
        self.taxonomies = []
        for k, v in data.items():
            setattr(self, k, v)


class RowValidationFormBase(forms.Form):
    # See descriptions, examples of the fields at https://docs.laws.africa/managing-works/bulk-imports-spreadsheet
    # core details
    country = forms.ChoiceField(required=True)
    locality = forms.ChoiceField(required=False)
    title = forms.CharField()
    doctype = forms.ChoiceField(required=True)
    subtype = forms.ChoiceField(required=False)
    number = forms.CharField(validators=[
        RegexValidator(r'^[a-zA-Z0-9-]+$', __("No spaces or punctuation allowed (use '-' for spaces)."))
    ])
    year = forms.CharField(validators=[
        RegexValidator(r'\d{4}', __('Must be a year (yyyy).'))
    ])
    # publication details
    publication_name = forms.CharField(required=False)
    publication_number = forms.CharField(required=False)
    publication_date = forms.DateField(error_messages={'invalid': __('Date format should be yyyy-mm-dd.')})
    # other relevant dates
    assent_date = forms.DateField(required=False, error_messages={'invalid': __('Date format should be yyyy-mm-dd.')})
    commencement_date = forms.DateField(required=False,
                                        error_messages={'invalid': __('Date format should be yyyy-mm-dd.')})
    # other info
    stub = forms.BooleanField(required=False)
    principal = forms.BooleanField(required=False)
    taxonomy = forms.CharField(required=False)
    # passive relationships
    primary_work = forms.CharField(required=False)
    commenced_by = forms.CharField(required=False)
    commenced_on_date = forms.DateField(required=False,
                                        error_messages={'invalid': __('Date format should be yyyy-mm-dd.')})
    amended_by = forms.CharField(required=False)
    amended_on_date = forms.DateField(required=False,
                                      error_messages={'invalid': __('Date format should be yyyy-mm-dd.')})
    repealed_by = forms.CharField(required=False)
    repealed_on_date = forms.DateField(required=False,
                                       error_messages={'invalid': __('Date format should be yyyy-mm-dd.')})
    # active relationships
    subleg = forms.CharField(required=False)
    commences = forms.CharField(required=False)
    commences_on_date = forms.DateField(required=False,
                                        error_messages={'invalid': __('Date format should be yyyy-mm-dd.')})
    amends = forms.CharField(required=False)
    amends_on_date = forms.DateField(required=False, error_messages={'invalid': __('Date format should be yyyy-mm-dd.')})
    repeals = forms.CharField(required=False)
    repeals_on_date = forms.DateField(required=False,
                                      error_messages={'invalid': __('Date format should be yyyy-mm-dd.')})

    def __init__(self, country, locality, subtypes, default_doctype, data=None, *args, **kwargs):
        self.default_doctype = default_doctype
        data = self.sanitize_incoming(data)
        super().__init__(data, *args, **kwargs)
        self.fields['country'].choices = [(country.code, country.name)]
        self.fields['locality'].choices = [(locality.code, locality.name)] \
            if locality else []
        self.fields['doctype'].choices = self.get_doctypes_for_country(country.code)
        self.fields['subtype'].choices = [(s.abbreviation, s.name) for s in subtypes]
        self.fields['publication_date'].required = not country.publication_date_optional

    def get_doctypes_for_country(self, country_code):
        return [[d[1].lower(), d[0]] for d in
                settings.INDIGO['DOCTYPES'] +
                settings.INDIGO['EXTRA_DOCTYPES'].get(country_code, [])]

    def sanitize_incoming(self, data):
        if data:
            data = data.copy()
            country = data.get('country', '')
            data['country'] = country.lower()
            locality = data.get('locality', '')
            data['locality'] = locality.lower()
            doctype = data.get('doctype', '')
            data['doctype'] = doctype.lower() or self.default_doctype
            subtype = data.get('subtype', '')
            data['subtype'] = subtype.lower()

        return data

    def clean_title(self):
        title = self.cleaned_data.get('title')
        return re.sub('[\u2028 ]+', ' ', title)


class ChapterMixin:
    """ Includes (optional) Chapter (cap) field.
    For this field to be recorded on bulk creation, add `'cap': 'Chapter (Cap.)'`
    for the relevant country in settings.INDIGO['WORK_PROPERTIES']
    """
    cap = forms.CharField(required=False)


@plugins.register('bulk-creator')
class BaseBulkCreator(LocaleBasedMatcher):
    """ Create works in bulk from a google sheets spreadsheet.
    """
    locale = (None, None, None)
    """ The locale this bulk creator is suited for, as ``(country, language, locality)``.
    """

    row_validation_form_class = RowValidationFormBase
    """ The validation form for each row of the spreadsheet. 
        Can be subclassed / mixed in to add fields or making existing fields optional.
    """

    aliases = []
    """ list of tuples of the form ('alias', 'meaning')
    (to be declared by subclasses), e.g. ('gazettement_date', 'publication_date')
    """

    default_doctype = 'act'
    """ If this is overridden by a subclass, the default doctype must be given in
        settings.INDIGO['EXTRA_DOCTYPES'] for the relevant country code, e.g.
        default_doctype = 'not_act'
        INDIGO['EXTRA_DOCTYPES'] = {
            'za': [('Not an Act', 'not_act')],
        }
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
            raise ValidationError(_("Error talking to Google Sheets: %s") % str(e))

        reader = csv.reader(io.StringIO(response.content.decode('utf-8')))
        rows = list(reader)

        if not rows or not rows[0]:
            raise ValidationError(_(
                "Your sheet did not import successfully; "
                "please check that you have link sharing ON (Anyone with the link)."
            ))
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
            raise ValidationError(
                _("Unable to access spreadsheet. Is the URL correct and have you shared it with %s?").format(
                    self._gsheets_secret['client_email'],
                ))

        rows = result.get('values', [])
        if not rows or not rows[0]:
            raise ValidationError(_("There doesn't appear to be data in sheet %(name)s of %(id)s") % {
                'name': sheet_name,
                'id': spreadsheet_id
            })
        return rows

    @property
    def gsheets_client(self):
        if not self._service:
            if not self._gsheets_secret:
                self._gsheets_secret = settings.INDIGO['GSHEETS_API_CREDS']
            credentials = service_account.Credentials.from_service_account_info(self._gsheets_secret, scopes=self.GSHEETS_SCOPES)
            self._service = build('sheets', 'v4', credentials=credentials)
        return self._service

    def get_row_validation_form(self, country, locality, subtypes, default_doctype, row_data):
        return self.row_validation_form_class(country, locality, subtypes, default_doctype, data=row_data)

    def get_rows_from_table(self, table):
        # clean up headers
        headers = [h.split(' ')[0].lower() for h in table[0]]

        # Transform rows into list of dicts for easy access.
        # The rows in table only have entries up to the last non-empty cell,
        # so we ensure that we have at least an empty string for every header.
        rows = [
            {header: (row[i].strip() if i < len(row) else '') for i, header in enumerate(headers) if header}
            for row in table[1:]
        ]

        # skip 'ignore' and blank rows
        rows = [r for r in rows if (not r.get('ignore')) and any(r.values())]

        return rows

    def create_works(self, table, dry_run, form_data):
        self.workflow = form_data.get('workflow')
        self.subtypes = Subtype.objects.all()
        self.dry_run = dry_run

        self.works = []

        rows = self.get_rows_from_table(table)

        for idx, row in enumerate(rows):
            self.works.append(self.create_work(row, idx))

        self.check_preview_duplicates()

        # link all commencements first so that amendments and repeals will have dates to work with (include duplicates)
        for row in self.works:
            if row.status and row.commenced:
                self.link_commencement_passive(row)
            if row.status and row.commences:
                self.link_commencement_active(row)

        for row in self.works:
            if row.status:
                # this will check duplicate works as well
                # (they won't overwrite the existing works but the relationships will be linked)
                if row.primary_work:
                    self.link_parent_work(row)

                if row.subleg:
                    self.link_children_works(row)

                if row.taxonomy:
                    self.link_taxonomy(row)

                if row.amended_by:
                    self.link_amendment_passive(row)

                if row.amends:
                    self.link_amendment_active(row)

                if row.repealed_by:
                    self.link_repeal_passive(row)

                if row.repeals:
                    self.link_repeal_active(row)

        return self.works

    def create_or_update(self, row):
        frbr_uri = self.get_frbr_uri(row)
        try:
            row.work = Work.objects.get(frbr_uri=frbr_uri)
            row.status = 'duplicate'

        except Work.DoesNotExist:
            work = Work()

            work.frbr_uri = frbr_uri
            work.country = self.country
            work.locality = self.locality
            for attribute in ['title',
                              'publication_name', 'publication_number',
                              'assent_date', 'publication_date',
                              'commenced', 'stub', 'principal']:
                setattr(work, attribute, getattr(row, attribute, None))
            work.created_by_user = self.user
            work.updated_by_user = self.user
            self.add_extra_properties(work, row)

            try:
                work.full_clean()
                work.set_frbr_uri_fields()
                if not self.dry_run:
                    work.save_with_revision(self.user)

                    # signals
                    if not self.testing:
                        work_changed.send(sender=work.__class__, work=work, request=self.request)

                # info for linking publication document
                row.params = {
                    'date': work.publication_date,
                    'number': work.publication_number,
                    'publication': work.publication_name,
                    'country': self.country.place_code,
                    'locality': self.locality.code if self.locality else None,
                }

                self.link_publication_document(work, row)

                if work.principal:
                    self.create_task(work, row, task_type='import-content')

                row.work = work
                row.status = 'success'

            except ValidationError as e:
                if hasattr(e, 'message_dict'):
                    row.errors = ' '.join(
                        ['%s: %s' % (f, '; '.join(errs)) for f, errs in e.message_dict.items()]
                    )
                else:
                    row.errors = str(e)

    def create_work(self, row, idx):
        # handle spreadsheet that still only uses 'principal'
        row['stub'] = row.get('stub') if 'stub' in row else not row.get('principal')
        row = self.validate_row(row)
        row.status = None
        row.row_number = idx + 2

        if row.errors:
            return row

        self.create_or_update(row)

        return row

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
            if meaning in errors.keys():
                errors[alias] = errors[meaning]
                errors.pop(meaning)

    def validate_row(self, row):
        self.transform_aliases(row)
        form = self.get_row_validation_form(self.country, self.locality, self.subtypes, self.default_doctype, row)
        errors = form.errors
        self.transform_error_aliases(errors)

        row = SpreadsheetRow(form.cleaned_data, errors)
        # has the work (implicitly) commenced?
        # if the commencement date has an error, the row won't have the attribute
        row.commenced = bool(
            getattr(row, 'commencement_date', None) or
            getattr(row, 'commenced_on_date', None) or
            row.commenced_by)

        # if commencement_date or commenced_on_date is set to any day in the year 9999, clear both
        if (getattr(row, 'commencement_date', None) and getattr(row, 'commencement_date').year == 9999) or \
                (getattr(row, 'commenced_on_date', None) and getattr(row, 'commenced_on_date').year == 9999):
            row.commencement_date = None
            row.commenced_on_date = None

        if self.dry_run:
            if not row.commenced:
                row.notes.append('Uncommenced')
            elif row.commenced and not row.commencement_date and not row.commenced_on_date:
                row.notes.append('Unknown commencement date')

            if row.stub:
                row.notes.append('Stub')
            if row.principal:
                row.notes.append('Principal work')

        return row

    def get_frbr_uri(self, row):
        frbr_uri = FrbrUri(country=row.country,
                           locality=row.locality,
                           doctype=row.doctype,
                           subtype=row.subtype,
                           date=row.year,
                           number=row.number,
                           actor=getattr(row, 'actor', None))

        return frbr_uri.work_uri().lower()

    def add_extra_properties(self, work, row):
        place = self.locality or self.country
        for extra_property in place.settings.work_properties.keys():
            if hasattr(row, extra_property):
                work.properties[extra_property] = str(getattr(row, extra_property) or '')

    def link_publication_document(self, work, row):
        locality_code = self.locality.code if self.locality else None
        finder = plugins.for_locale('publications', self.country.code, None, locality_code)

        if not finder or not row.params.get('date'):
            return self.create_task(work, row, task_type='link-gazette')

        try:
            publications = finder.find_publications(row.params)
        except requests.HTTPError:
            return self.create_task(work, row, task_type='link-gazette')

        if len(publications) != 1:
            return self.create_task(work, row, task_type='link-gazette')

        if not self.dry_run:
            pub_doc_details = publications[0]
            pub_doc = PublicationDocument()
            pub_doc.work = work
            pub_doc.file = None
            pub_doc.trusted_url = pub_doc_details.get('url')
            pub_doc.size = pub_doc_details.get('size')
            pub_doc.save()

    def check_preview_duplicates(self):
        if self.dry_run:
            frbr_uris = [row.work.frbr_uri for row in self.works if hasattr(row, 'work')]
            for row in self.works:
                if hasattr(row, 'work') and frbr_uris.count(row.work.frbr_uri) > 1:
                    row.notes.append('Duplicate in batch')

    def link_commencement_passive(self, row):
        # if the work has commencement details, try linking it
        # make a task if a `commenced_by` FRBR URI is given but not found
        date = row.commenced_on_date or row.commencement_date

        commencing_work = None
        if row.commenced_by:
            commencing_work = self.find_work(row.commenced_by)
            if not commencing_work:
                row.work.commenced = False
                return self.create_task(row.work, row, task_type='link-commencement-passive')

            row.relationships.append(f'Commenced by {commencing_work} on {date or "(unknown)"}')

        if not self.dry_run:
            if row.status == 'duplicate' and not row.work.commenced:
                # follow 'rationalise' logic from Commencement model
                row.work.commenced = True
                row.work.updated_by_user = self.user
                row.work.save()

            Commencement.objects.get_or_create(
                commenced_work=row.work,
                commencing_work=commencing_work,
                date=date,
                defaults={
                    'main': True,
                    'all_provisions': True,
                    'created_by_user': self.user,
                },
            )

    def link_commencement_active(self, row):
        # if the work `commences` another work, try linking it
        # make a task if a `commences` FRBR URI is given but not found,
        # or if a `commences_on_date` wasn't given
        date = row.commences_on_date
        if not date:
            return self.create_task(row.work, row, task_type='commences-on-date-missing')

        commenced_work = self.find_work(row.commences)
        if not commenced_work:
            return self.create_task(row.work, row, task_type='link-commencement-active')

        row.relationships.append(f'Commences {commenced_work} on {date}')
        for row in self.works:
            if 'Uncommenced' in row.notes and \
                    ((hasattr(row, 'work') and
                      (row.work == commenced_work or
                       isinstance(commenced_work, str) and row.work.frbr_uri == commenced_work.split()[0])) or
                     hasattr(row, 'frbr_uri') and isinstance(commenced_work, str) and row.frbr_uri == commenced_work.split()[0]):
                row.notes.remove('Uncommenced')

        if not self.dry_run:
            if not commenced_work.commenced:
                # follow 'rationalise' logic from Commencement model
                commenced_work.commenced = True
                commenced_work.updated_by_user = self.user
                commenced_work.save()

            Commencement.objects.get_or_create(
                commenced_work=commenced_work,
                commencing_work=row.work,
                date=date,
                defaults={
                    'main': True,
                    'all_provisions': True,
                    'created_by_user': self.user,
                },
            )
            self.update_works_list(commenced_work)

    def link_repeal_passive(self, row):
        # if the work is `repealed_by` something, try linking it or make the relevant task
        repealing_work = self.find_work(row.repealed_by)

        if not repealing_work:
            # a work with the given FRBR URI / title wasn't found
            self.create_task(row.work, row, task_type='no-repealed-by-match')

        elif row.work.repealed_by and row.work.repealed_by != repealing_work:
            # the work was already marked as repealed by a different work
            self.create_task(row.work, row, task_type='check-update-repeal',
                             repealing_work=repealing_work)

        elif not row.work.repealed_by:
            # the work was not already repealed; link the new repeal information
            row.relationships.append(f'Repealed by {repealing_work}')
            if not self.dry_run:
                repeal_date = row.repealed_on_date or repealing_work.commencement_date

                if not repeal_date:
                    # there's no date for the repeal (yet), so create a task on the repealing work for once it commences
                    return self.create_task(repealing_work, row,
                                            task_type='link-repeal-pending-commencement', repealed_work=row.work)

                row.work.repealed_by = repealing_work
                row.work.repealed_date = repeal_date

                try:
                    row.work.save_with_revision(self.user)
                except ValidationError:
                    # something else went wrong
                    self.create_task(row.work, row, task_type='link-repeal',
                                     repealing_work=repealing_work)

    def link_repeal_active(self, row):
        # if the work `repeals` something, try linking it or make the relevant task
        repealed_work = self.find_work(row.repeals)

        if not repealed_work:
            # a work with the given FRBR URI / title wasn't found
            return self.create_task(row.work, row, task_type='no-repeals-match')

        elif isinstance(repealed_work, Work) and \
                repealed_work.repealed_by and repealed_work.repealed_by != row.work:
            # the repealed work was already marked as repealed by a different work
            return self.create_task(repealed_work, row, task_type='check-update-repeal',
                                    repealing_work=row.work)

        if isinstance(repealed_work, Work) and not repealed_work.repealed_by or self.dry_run:
            # the work was not already repealed (or we're in preview); link the new repeal information
            repeal_date = row.repeals_on_date or row.commencement_date
            row.relationships.append(f'Repeals {repealed_work}')

            if not repeal_date:
                # there's no date for the repeal (yet), so create a task on the repealing work for once it commences
                return self.create_task(row.work, row,
                                        task_type='link-repeal-pending-commencement', repealed_work=repealed_work)

            if not self.dry_run:
                repealed_work.repealed_by = row.work
                repealed_work.repealed_date = repeal_date

                try:
                    repealed_work.save_with_revision(self.user)
                    self.update_works_list(repealed_work)
                except ValidationError:
                    # something else went wrong
                    self.create_task(repealed_work, row, task_type='link-repeal',
                                     repealing_work=row.work)

    def link_parent_work(self, row):
        # if the work has a `primary_work`, try linking it
        # make a task if this fails
        parent_work = self.find_work(row.primary_work)
        if not parent_work:
            return self.create_task(row.work, row, task_type='link-primary-work')

        row.relationships.append(f'Subleg under {parent_work}')
        if not self.dry_run:
            row.work.parent_work = parent_work
            try:
                row.work.save_with_revision(self.user)
            except ValidationError:
                self.create_task(row.work, row, task_type='link-primary-work')

    def link_children_works(self, row):
        # if the work has `subleg`, try linking them
        # make a task if this fails
        subleg = [x.strip() for x in row.subleg.split(';') if x.strip()]
        for child_str in subleg:
            child = self.find_work(child_str)
            if not child:
                self.create_task(row.work, row, task_type='link-subleg', subleg=child_str)

            elif not isinstance(child, Work) or not child.parent_work:
                row.relationships.append(f'Primary work of {child}')

            if isinstance(child, Work):
                if child.parent_work:
                    # the child already has a parent work
                    if self.dry_run:
                        row.notes.append(f'{child} already has a primary work')
                    else:
                        self.create_task(child, row, task_type='check-update-primary', main_work=row.work)
                    continue

                elif not self.dry_run:
                    child.parent_work = row.work
                    try:
                        child.save_with_revision(self.user)
                        self.update_works_list(child)
                    except ValidationError:
                        self.create_task(row.work, row, task_type='link-subleg', subleg=child_str)

    def link_amendment_passive(self, row):
        # if the work is `amended_by` something, try linking it
        # (this will only work if there's only one amendment listed)
        # make a task if this fails
        amending_work = self.find_work(row.amended_by)
        if not amending_work:
            return self.create_task(row.work, row, task_type='link-amendment-passive')


        if self.dry_run:
            row.relationships.append(f'Amended by {amending_work}')
            row.notes.append("An 'Apply amendment' task will be created on this work")
        else:
            date = row.amended_on_date or amending_work.commencement_date
            if not date:
                return self.create_task(amending_work, row,
                                        task_type='link-amendment-pending-commencement',
                                        amended_work=row.work)

            row.relationships.append(f'Amended by {amending_work} on {date}')

            amendment, new = Amendment.objects.get_or_create(
                amended_work=row.work,
                amending_work=amending_work,
                date=date,
                defaults={
                    'created_by_user': self.user,
                },
            )

            if new:
                self.create_task(row.work, row,
                                 task_type='apply-amendment',
                                 amendment=amendment)

    def link_amendment_active(self, row):
        # if the work `amends` something, try linking it
        # (this will only work if there's only one amendment listed)
        # make a task if this fails
        amended_work = self.find_work(row.amends)
        if not amended_work:
            return self.create_task(row.work, row, task_type='link-amendment-active')

        date = row.amends_on_date or row.commencement_date or row.work.commencement_date
        if not date:
            return self.create_task(row.work, row,
                                    task_type='link-amendment-pending-commencement',
                                    amended_work=amended_work)

        row.relationships.append(f'Amends {amended_work} on {date}')
        if self.dry_run:
            row.notes.append(f"An 'Apply amendment' task will be created on {amended_work}")
        else:
            amendment, new = Amendment.objects.get_or_create(
                amended_work=amended_work,
                amending_work=row.work,
                date=date,
                defaults={
                    'created_by_user': self.user,
                },
            )

            if new:
                self.create_task(amended_work, row,
                                 task_type='apply-amendment',
                                 amendment=amendment)

    def link_taxonomy(self, row):
        topics = [x.strip() for x in row.taxonomy.split(';') if x.strip()]
        unlinked_topics = []
        for t in topics:
            topic = VocabularyTopic.get_topic(t)
            if topic:
                row.taxonomies.append(topic)
                if not self.dry_run:
                    row.work.taxonomies.add(topic)
                    row.work.save_with_revision(self.user)

            else:
                unlinked_topics.append(t)
        if unlinked_topics:
            if self.dry_run:
                row.notes.append(f'Taxonomy not found: {"; ".join(unlinked_topics)}')
            else:
                row.unlinked_topics = "; ".join(unlinked_topics)
                try:
                    existing_task = Task.objects.get(work=row.work, code='link-taxonomy', description__contains=row.unlinked_topics)
                except Task.DoesNotExist:
                    self.create_task(row.work, row, task_type='link-taxonomy')

    def create_task(self, work, row, task_type, repealing_work=None, repealed_work=None, amended_work=None, amendment=None, subleg=None, main_work=None):
        if self.dry_run:
            row.tasks.append(task_type.replace('-', ' '))
            return

        task = Task()

        if task_type == 'link-gazette':
            task.title = _('Link gazette')
            task.description = _('''This work's gazette (original publication document) couldn't be linked automatically.

Find it and upload it manually.''')

        elif task_type == 'import-content':
            task.title = _('Import content')
            task.description = _('Import the content for this work – either the initial publication (usually a PDF of the Gazette) or a later consolidation (usually a .docx file).')

        elif task_type == 'link-commencement-passive':
            task.title = _('Link commencement (passive)')
            task.description = _('''It looks like this work was commenced by "%(commenced_by)s" on %(date)s (see row %(row_num)s of the spreadsheet), but it couldn't be linked automatically. This work has thus been recorded as 'Not commenced'.

Possible reasons:
– a typo in the spreadsheet
– the commencing work doesn't exist on the system.

Please link the commencement date and commencing work manually.''') % {
                'commenced_by': row.commenced_by,
                'date': row.commenced_on_date or row.commencement_date or _("(unknown)"),
                'row_num': row.row_number,
            }

        elif task_type == 'commences-on-date-missing':
            task.title = _("'Commences on' date missing")
            task.description = _('''It looks like this work commences "%(commences)s" (see row %(row_num)s of the spreadsheet), but 'commences_on_date' wasn't given so no action has been taken.

If it should be linked, please do so manually.''') % {
                'commences': row.commences,
                'row_num': row.row_number,
            }

        elif task_type == 'link-commencement-active':
            task.title = _('Link commencement (active)')
            task.description = _('''It looks like this work commences "%(commences)s" on %(date)s (see row %(row_num)s of the spreadsheet), but "%(commences)s" wasn't found, so no action has been taken.

Possible reasons:
– a typo in the spreadsheet
– the commenced work doesn't exist on the system.

If the commencement should be linked, please do so manually.''') % {
                'commences': row.commences,
                'date': row.commenced_on_date,
                'row_num': row.row_number,
            }

        elif task_type == 'link-amendment-active':
            task.title = _('Link amendment (active)')
            amended_work = row.amends
            if len(amended_work) > 256:
                amended_work = "".join(amended_work[:256] + ', etc')
            task.description = _('''It looks like this work amends "%(amended_work)s" (see row %(row_num)s of the spreadsheet), but it couldn't be linked automatically.

Possible reasons:
– a typo in the spreadsheet
– more than one amended work was listed (it only works if there's one)
– the amended work doesn't exist on the system.

Please link the amendment manually.''') % {
                'amended_work': amended_work,
                'row_num': row.row_number,
            }

        elif task_type == 'link-amendment-passive':
            task.title = _('Link amendment (passive)')
            amending_work = row.amended_by
            if len(amending_work) > 256:
                amending_work = "".join(amending_work[:256] + ', etc')
            task.description = _('''It looks like this work is amended by "%(amending_work)s" (see row %(row_num)s of the spreadsheet), but it couldn't be linked automatically.

Possible reasons:
– a typo in the spreadsheet
– more than one amending work was listed (it only works if there's one)
– the amending work doesn't exist on the system.

Please link the amendment manually.''') % {
                'amending_work': amending_work,
                'row_num': row.row_number,
            }

        elif task_type == 'link-amendment-pending-commencement':
            task.title = _('Link amendment (pending commencement)')
            task.description = _('''It looks like this work amends %(amended_title)s (%(numbered_title)s), but it couldn't be linked automatically because this work hasn't commenced yet (so there's no date for the amendment).

Please link the amendment manually (and apply it) when this work comes into force.''') % {
                'amended_title': amended_work.title,
                'numbered_title': amended_work.numbered_title(),
            }

        elif task_type == 'apply-amendment':
            task.title = _('Apply amendment')
            task.description = _('''Apply the amendments made by %(amending_title)s (%(numbered_title)s) on %(date)s.

The amendment has already been linked, so start at Step 3 of https://docs.laws.africa/managing-works/amending-works.''') % {
                'amending_title': amendment.amending_work.title,
                'numbered_title': amendment.amending_work.numbered_title(),
                'date': amendment.date,
            }

        elif task_type == 'no-repealed-by-match':
            task.title = _('Link repealed by')
            task.description = _('''It looks like this work was repealed by "%(repealed_by)s" (see row %(row_num)s of the spreadsheet), but it couldn't be linked automatically.

Possible reasons:
– a typo in the spreadsheet
– the repealing work doesn't exist on the system.

Please link the repeal manually.''') % {
                'repealed_by': row.repealed_by,
                'row_num': row.row_number,
            }

        elif task_type == 'no-repeals-match':
            task.title = _('Link repeal')
            task.description = _('''It looks like this work repeals "%(repeals)s" (see row %(row_num)s of the spreadsheet), but it couldn't be linked automatically.

Possible reasons:
– a typo in the spreadsheet
– the repealed work doesn't exist on the system.

Please link the repeal manually.''') % {
                'repeals': row.repeals,
                'row_num': row.row_number,
            }

        elif task_type == 'check-update-repeal':
            task.title = _('Check / update repeal')
            task.description = _('''On the spreadsheet (see row %(row_num)s), it says that this work was repealed by %(repealing_title)s (%(repealing_numbered_title)s).

But this work is already listed as having been repealed by %(repealed_by)s (%(repealed_by_numbered_title)s), so the repeal information wasn't updated automatically.

If the old / existing repeal information was wrong, update it manually. Otherwise (if the spreadsheet was wrong), cancel this task with a comment.
''') % {
                'repealing_title': repealing_work.title,
                'repealing_numbered_title': repealing_work.numbered_title(),
                'repealed_by': work.repealed_by,
                'repealed_by_numbered_title': work.repealed_by.numbered_title(),
                'row_num': row.row_number,
            }

        elif task_type == 'link-repeal-pending-commencement':
            task.title = _('Link repeal (pending commencement)')
            task.description = _('''It looks like this work repeals %(title)s (%(numbered_title)s), but it couldn't be linked automatically because this work hasn't commenced yet (so there's no date for the repeal).

Please link the repeal manually when this work comes into force.''') % {
                'title': repealed_work.title,
                'numbered_title': repealed_work.numbered_title(),
            }

        elif task_type == 'link-repeal':
            task.title = _('Link repeal')
            task.description = _('''It looks like this work was repealed by %(title)s (%(numbered_title)s), but it couldn't be linked automatically.

Please link it manually.''') % {
                'title': repealing_work.title,
                'numbered_title': repealing_work.numbered_title(),
            }

        elif task_type == 'link-primary-work':
            task.title = _('Link primary work')
            task.description = _('''It looks like this work's primary work is "%(work)s" (see row %(row_num)s of the spreadsheet), but it couldn't be linked automatically.

Possible reasons:
– a typo in the spreadsheet
– the primary work doesn't exist on the system.

Please link the primary work manually.''') % {
                'work': row.primary_work,
                'row_num': row.row_number,
            }

        elif task_type == 'link-subleg':
            task.title = _('Link subleg')
            task.description = _('''It looks like this work has subleg "%(subleg)s" (see row %(row_num)s of the spreadsheet), but it couldn't be linked automatically.

Possible reasons:
– a typo in the spreadsheet
– the subleg work doesn't exist on the system.

Please link the subleg work manually.''') % {
                'subleg': subleg,
                'row_num': row.row_number,
            }

        elif task_type == 'check-update-primary':
            task.title = _('Check / update primary work')
            task.description = _('''On the spreadsheet (see row %(row_num)s), it says that this work is subleg under %(title)s (%(numbered_title)s).

But this work is already subleg under %(parent)s, so nothing was done.

Double-check which work this work is subleg of and update it manually if needed. If the spreadsheet was wrong, cancel this task with a comment.''') % {
                'title': main_work.title,
                'numbered_title': main_work.numbered_title(),
                'parent': work.parent_work.title,
                'row_num': row.row_number,
            }

        elif task_type == 'link-taxonomy':
            task.title = _('Link taxonomy')
            task.description = _(f'''It looks like this work has the following taxonomy: "%(topics)s" (see row %(row_num)s of the spreadsheet), but it couldn't be linked automatically.

Possible reasons:
– a typo in the spreadsheet
– the taxonomy doesn't exist on the system.''') % {
                'topics': row.unlinked_topics,
                'row_num': row.row_number,
            }

        task.country = self.country
        task.locality = self.locality
        task.work = work
        task.code = task_type
        task.created_by_user = self.user

        # need to save before assigning workflow because of M2M relation
        task.save()
        if self.workflow:
            task.workflows.set([self.workflow])
            task.save()

        if 'pending-commencement' in task_type:
            # add the `pending commencement` label, if it exists
            pending_commencement_label = TaskLabel.objects.filter(slug='pending-commencement').first()
            if pending_commencement_label:
                task.labels.add(pending_commencement_label)
                task.save()

        return task

    def find_work(self, given_string):
        """ The string we get from the spreadsheet could be e.g.
            `/ug/act/1933/14 - Administrator-General’s Act` (new and preferred style)
            `Administrator-General’s Act` (old style)
            First see if the string before the first space can be parsed as an FRBR URI, and find a work based on that.
            If not, assume a title has been given and try to match on the whole string.
            In the case of a dry run, return a string if the work hasn't been found.
        """
        work = None
        substring = given_string.split()[0]
        try:
            FrbrUri.parse(substring)
            work = Work.objects.filter(frbr_uri=substring).first()
        except ValueError:
            potential_matches = Work.objects.filter(title=given_string, country=self.country, locality=self.locality)
            if len(potential_matches) == 1:
                work = potential_matches.first()
        if self.dry_run and not work:
            # neither the FRBR URI nor the title matched,
            # but it could be in the current batch
            for row in self.works:
                if hasattr(row, 'work') and (substring == row.work.frbr_uri or given_string == row.work.title):
                    work = _('%s (about to be imported)') % given_string
                    break
        return work

    @property
    def share_with(self):
        if not self._gsheets_secret:
            self._gsheets_secret = settings.INDIGO['GSHEETS_API_CREDS']

        return self._gsheets_secret.get('client_email')

    def update_works_list(self, work):
        """ Replaces a work in self.works with the updated one.
            Use whenever a reverse-relationship work is updated.
        """
        for row in self.works:
            if hasattr(row, 'work') and row.work.pk == work.pk:
                row.work = work


@plugins.register('bulk-updater')
class BaseBulkUpdater(BaseBulkCreator):
    """ Update works in bulk from a google sheets spreadsheet.
    """
    # TODO: get these core fields from somewhere else? cobalt / FRBR URI fields?
    core_fields = ['actor', 'country', 'locality', 'doctype', 'subtype', 'number', 'year']
    update_columns = None

    def get_rows_from_table(self, table):
        """ Differs from parent method in that only the selected columns and core fields are included for each row.
        """
        # clean up headers
        headers = [h.split(' ')[0].lower() for h in table[0]]

        # Transform rows into list of dicts for easy access.
        # The rows in table only have entries up to the last non-empty cell,
        # so we ensure that we have at least an empty string for every header.
        columns = self.update_columns + self.core_fields
        rows = []
        for row in table[1:]:
            row_dict = {}
            ignore = False
            for i, header in enumerate(headers):
                value = row[i].strip() if i < len(row) else ''
                if header == 'ignore' and value:
                    ignore = True
                    break
                if header and header in columns:
                    row_dict[header] = value
            # skip 'ignore' and blank rows
            if not ignore and any(row_dict.values()):
                rows.append(row_dict)

        return rows

    def create_works(self, table, dry_run, form_data):
        self.update_columns = form_data.get('update_columns')
        super().create_works(table, dry_run, form_data)

    def create_or_update(self, row):
        frbr_uri = self.get_frbr_uri(row)
        try:
            work = Work.objects.get(frbr_uri=frbr_uri)
            # TODO:
            #  - update relevant columns (self.update_columns)
            #  - stash old values where changed to show in Preview; use a form?

            row.work = work
            row.status = 'success'

        except Work.DoesNotExist as e:
            # TODO:
            #  - add error message
            #  - add a new status, or reuse 'duplicate' and tweak template?
            row.errors = []
            return row

    def validate_row(self, row):
        # TODO: cut down on repetition
        self.transform_aliases(row)

        # lowercase country, locality, doctype and subtype
        row['country'] = row.get('country', '').lower()
        row['locality'] = row.get('locality', '').lower()
        row['doctype'] = row.get('doctype', '').lower() or self.default_doctype
        row['subtype'] = row.get('subtype', '').lower()

        form = self.get_row_validation_form(self.country, self.locality, self.subtypes, row)

        errors = form.errors
        self.transform_error_aliases(errors)

        # TODO: only care about core_fields and update_columns: don't set other attributes
        #  - subclass SpreadsheetRow?
        #  - or manipulate form.cleaned_data before instantiating?
        row = SpreadsheetRow(form.cleaned_data, errors)
        # has the work (implicitly) commenced?
        # if the commencement date has an error, the row won't have the attribute
        row.commenced = bool(
            getattr(row, 'commencement_date', None) or
            getattr(row, 'commenced_on_date', None) or
            row.commenced_by)

        # if commencement_date or commenced_on_date is set to any day in the year 9999, clear both
        if (getattr(row, 'commencement_date', None) and getattr(row, 'commencement_date').year == 9999) or \
                (getattr(row, 'commenced_on_date', None) and getattr(row, 'commenced_on_date').year == 9999):
            row.commencement_date = None
            row.commenced_on_date = None

        if self.dry_run:
            if not row.commenced:
                row.notes.append('Uncommenced')
            elif row.commenced and not row.commencement_date and not row.commenced_on_date:
                row.notes.append('Unknown commencement date')

            if row.stub:
                row.notes.append('Stub')
            if row.principal:
                row.notes.append('Principal work')

        return row

    def check_preview_duplicates(self):
        # TODO: how do we want to treat duplicates during update?
        pass
