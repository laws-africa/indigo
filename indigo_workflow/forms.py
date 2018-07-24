from django import forms

from indigo_app.models import Country
from indigo_api.models import Amendment

from .models import ImplicitPlaceProcess, CreatePointInTimeProcess


class ImplicitPlaceProcessForm(forms.ModelForm):
    class Meta:
        model = ImplicitPlaceProcess
        fields = ['notes', 'country', 'locality']

    country = forms.ModelChoiceField(queryset=Country.objects.select_related('country'))
    locality = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super(ImplicitPlaceProcessForm, self).clean()
        if cleaned_data.get('locality'):
            cleaned_data['locality'] = cleaned_data['country'].locality_set.filter(code=cleaned_data['locality']).first()
        return cleaned_data


class CreatePointInTimeProcessForm(forms.ModelForm):
    class Meta:
        model = CreatePointInTimeProcess
        fields = ['work', 'amendment', 'date', 'language']

    amendment = forms.ModelChoiceField(queryset=Amendment.objects, required=False)

    def clean(self):
        cleaned_data = super(CreatePointInTimeProcessForm, self).clean()

        # ensure amendment is bound to the work at the right date
        if cleaned_data.get('amendment'):
            amendment = cleaned_data['amendment']
            if (amendment.work != cleaned_data['work'] or amendment.date != cleaned_data['date']):
                del cleaned_data['amendment']

        # try to find an amendment matching the given date
        if cleaned_data.get('amendment') is None:
            cleaned_data['amendment'] = cleaned_data['work'].amendments.filter(date=cleaned_data['date']).first()

        return cleaned_data
