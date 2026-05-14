from allauth.account.forms import SignupForm
from django_recaptcha.fields import ReCaptchaField
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from indigo_api.models import Country
from indigo_app.models import Editor


class UserEditorForm(forms.ModelForm):
    first_name = forms.CharField(label=_('First name'))
    last_name = forms.CharField(label=_('Last name'))
    language = forms.ChoiceField(label=_('Language'), choices=settings.LANGUAGES)

    class Meta:
        model = Editor
        fields = ('country', 'language')

    def save(self, commit=True):
        super().save()
        self.instance.user.first_name = self.cleaned_data['first_name']
        self.instance.user.last_name = self.cleaned_data['last_name']
        self.instance.user.save()


class UserSignupForm(SignupForm):
    first_name = forms.CharField(required=True, max_length=30, label=_('First name'))
    last_name = forms.CharField(required=True, max_length=30, label=_('Last name'))
    captcha = ReCaptchaField()
    signup_enabled = settings.ACCOUNT_SIGNUP_ENABLED

    def clean(self):
        if not self.signup_enabled:
            raise forms.ValidationError(_("Creating new accounts is currently not allowed."))
        return super().clean()
