import json

from django import forms

from indigo_api.models import Document, Language


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        exclude = ('document_xml', 'created_at', 'updated_at', 'created_by_user', 'updated_by_user',)


class ImportDocumentForm(forms.Form):
    file = forms.FileField()
    language = forms.ModelChoiceField(Language.objects)
    expression_date = forms.DateField()
    page_nums = forms.CharField(required=False)
    # options as JSON data
    options = forms.CharField(required=False)

    def clean_options(self):
        val = self.cleaned_data['options']
        try:
            return json.loads(val or '{}')
        except ValueError:
            raise forms.ValidationError("Invalid json data")
