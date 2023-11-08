from django import forms
from cobalt import FrbrUri


class WorkAdminForm(forms.ModelForm):
    frbr_uri = forms.CharField(required=False, disabled=True)

    def get_frbr_uri(self, cleaned_data):

        try:
            frbr_uri = FrbrUri(country=cleaned_data.get("country").code,
                               locality=cleaned_data.get("locality"),
                               doctype=cleaned_data.get("doctype"),
                               subtype=cleaned_data.get("subtype"),
                               date=cleaned_data.get("date"),
                               number=cleaned_data.get("number"),
                               actor=cleaned_data.get("actor"),
                               )
            return frbr_uri.work_uri().lower()
        except (ValueError, AttributeError) as e:
            raise forms.ValidationError("Cannot create FRBR URI") from e

    # def clean_country(self):
    #     country = self.cleaned_data.get("country")
    #     if country:
    #         return country
    #     return self.instance.country

    def clean(self):
        cleaned_data = super().clean()
        frbr_uri = self.get_frbr_uri(cleaned_data)
        cleaned_data["frbr_uri"] = frbr_uri
        return cleaned_data


class NewWorkFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["skip_signoff"] = forms.BooleanField(required=False)
        self.fields["block_import_task"] = forms.BooleanField(required=False)

    @classmethod
    def adjust_fields(cls, fields, remove=None):
        if fields:
            return fields + ["skip_signoff", "block_import_task"]

    @classmethod
    def remove_fields(cls, fields):
        if fields:
            return [f for f in fields if f not in ["skip_signoff", "block_import_task"]]
        return fields



