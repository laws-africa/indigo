from django import forms

from indigo_app.models import Country

from .models import ImplicitPlaceProcess


class ImplicitPlaceProcessForm(forms.ModelForm):
    class Meta:
        model = ImplicitPlaceProcess
        fields = ['notes', 'country']

    country = forms.ModelChoiceField(queryset=Country.objects.select_related('country').all())
