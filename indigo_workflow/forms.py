from django import forms

from indigo_app.models import Country

from .models import ImplicitPlaceProcess


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
