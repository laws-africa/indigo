from django import forms

from indigo_api.models import AmendmentInstruction


class AmendmentInstructionForm(forms.ModelForm):
    class Meta:
        model = AmendmentInstruction
        fields = [
            'language',
            'amending_provision',
            'title',
            'page_number',
            'provision_name',
            'amendment_instruction',
        ]

    def save(self, commit=True):
        self.instance.determine_provision_id()
        return super().save(commit)
