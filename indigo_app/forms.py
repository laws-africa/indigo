from django.forms import ModelForm

from indigo_api.models import Document

class DocumentForm(ModelForm):
    class Meta:
        model = Document
        exclude = ('document_xml', 'created_at', 'updated_at', 'created_by_user', 'updated_by_user',)
