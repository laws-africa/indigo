from django import forms

from indigo_api.models import AmendmentInstruction


class AmendmentInstructionForm(forms.ModelForm):
    class Meta:
        model = AmendmentInstruction
        fields = [
            'amending_provision',
            'title',
            'page_number',
            'provision_name',
            'amendment_instruction',
        ]
