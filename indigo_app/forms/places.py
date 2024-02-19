import re

from django import forms
from django.contrib.auth.models import User
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from lxml import etree

from indigo_api.models import Country, PlaceSettings
from indigo_app.forms.mixins import FormAsUrlMixin


class PlaceSettingsForm(forms.ModelForm):
    class Meta:
        model = PlaceSettings
        fields = ('spreadsheet_url', 'as_at_date', 'styleguide_url', 'no_publication_document_text',
                  'consolidation_note', 'is_consolidation', 'uses_chapter', 'publication_date_optional')

    spreadsheet_url = forms.URLField(required=False, validators=[
        URLValidator(
            schemes=['https'],
            regex='^https:\/\/docs.google.com\/spreadsheets\/d\/\S+\/[\w#=]*',
            message="Please enter a valid Google Sheets URL, such as https://docs.google.com/spreadsheets/d/ABCXXX/", code='bad')
    ])

    def clean_spreadsheet_url(self):
        url = self.cleaned_data.get('spreadsheet_url')
        return re.sub('/[\w#=]*$', '/', url)


class PlaceUsersForm(forms.Form):
    # make choices a lambda so that it's evaluated at runtime, not import time
    choices = lambda: [(u.id, (u.get_full_name() or u.username)) for u in User.objects.filter(badges_earned__slug='editor')]
    users = forms.MultipleChoiceField(choices=choices, label="Users with edit permissions", required=False, widget=forms.CheckboxSelectMultiple)


class CountryAdminForm(forms.ModelForm):
    italics_terms = SimpleArrayField(forms.CharField(max_length=1024, required=False), delimiter='\n', required=False, widget=forms.Textarea)

    class Meta:
        model = Country
        exclude = []

    def clean_italics_terms(self):
        # strip blanks and duplications
        return sorted(list(set(x for x in self.cleaned_data['italics_terms'] if x)))


class ExplorerForm(forms.Form, FormAsUrlMixin):
    xpath = forms.CharField(required=True)
    parent = forms.ChoiceField(choices=[('', 'None'), ('1', '1 level'), ('2', '2 levels')], required=False)
    localities = forms.BooleanField(required=False)
    global_search = forms.BooleanField(required=False)

    def clean_xpath(self):
        value = self.cleaned_data['xpath']

        try:
            etree.XPath(value)
        except etree.XPathError as e:
            raise ValidationError(str(e))

        return value
