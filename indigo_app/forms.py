from django.forms import ModelForm
from django.core.validators import URLValidator
from django import forms

from indigo_api.models import Document
from indigo_app.models import Country


class DocumentForm(ModelForm):
    class Meta:
        model = Document
        exclude = ('document_xml', 'created_at', 'updated_at', 'created_by_user', 'updated_by_user',)


class BatchCreateWorkForm(forms.Form):

    country = forms.ModelChoiceField(required=True, queryset=Country.objects, empty_label="Choose a country")

    spreadsheet_url = forms.URLField(required=True, validators=[
        URLValidator(
            schemes=['https'],
            regex='^https:\/\/docs.google.com\/spreadsheets\/d\/\S+\/',
            message="Please enter a valid Google Sheets URL, such as https://docs.google.com/spreadsheets/d/ABCXXX/", code='bad')
    ])
