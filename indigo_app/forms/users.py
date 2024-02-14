from allauth.account.forms import SignupForm
from captcha.fields import ReCaptchaField
from django import forms
from django.conf import settings

from indigo_api.models import Country
from indigo_app.models import Editor


class UserEditorForm(forms.ModelForm):
    first_name = forms.CharField(label='First name')
    last_name = forms.CharField(label='Last name')
    language = forms.ChoiceField(label='Language', choices=settings.LANGUAGES)

    class Meta:
        model = Editor
        fields = ('country', 'language')

    def save(self, commit=True):
        super().save()
        self.instance.user.first_name = self.cleaned_data['first_name']
        self.instance.user.last_name = self.cleaned_data['last_name']
        self.instance.user.save()


class UserSignupForm(SignupForm):
    first_name = forms.CharField(required=True, max_length=30, label='First name')
    last_name = forms.CharField(required=True, max_length=30, label='Last name')
    country = forms.ModelChoiceField(required=True, queryset=Country.objects, label='Country', empty_label=None)
    captcha = ReCaptchaField()
    accepted_terms = forms.BooleanField(required=True, initial=False, error_messages={
        'required': 'Please accept the Terms of Use.',
    })
    signup_enabled = settings.ACCOUNT_SIGNUP_ENABLED

    def clean(self):
        if not self.signup_enabled:
            raise forms.ValidationError("Creating new accounts is currently not allowed.")
        return super().clean()

    def save(self, request):
        user = super().save(request)
        user.editor.accepted_terms = True
        user.editor.country = self.cleaned_data['country']
        user.editor.save()
        return user
