from django.forms import ModelForm
from django.contrib.auth.models import User
from captcha.fields import ReCaptchaField
from allauth.account.forms import SignupForm

from indigo_app.models import Editor
from indigo_api.models import Document

class DocumentForm(ModelForm):
    class Meta:
        model = Document
        exclude = ('document_xml', 'created_at', 'updated_at', 'created_by_user', 'updated_by_user',)


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')


class UserProfileForm(ModelForm):
    class Meta:
        model = Editor
        fields = ('country',)


class UserSignupForm(SignupForm):
    captcha = ReCaptchaField()
