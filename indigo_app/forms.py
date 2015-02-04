from django.forms import ModelForm

from indigo_api.models import Document

class DocumentForm(ModelForm):
    class Meta:
        model = Document
