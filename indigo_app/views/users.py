from django.conf import settings
from django.views.generic import DetailView, UpdateView
from django.urls import reverse
from allauth.utils import get_request_param

from indigo_app.forms import UserEditorForm
from indigo_app.models import Editor
from .base import AbstractAuthedIndigoView


class EditAccountView(AbstractAuthedIndigoView, UpdateView):
    model = Editor
    template_name = 'indigo_app/user_account/edit.html'
    form_class = UserEditorForm

    def get_success_url(self):
        return reverse('edit_account')

    def get_form_kwargs(self):
        kwargs = super(EditAccountView, self).get_form_kwargs()
        kwargs['instance'] = self.request.user.editor
        return kwargs

    def get_object(self, queryset=None):
        return self.request.user.editor

    def get_initial(self):
        initial = super(EditAccountView, self).get_initial()
        initial['first_name'] = self.request.user.first_name
        initial['last_name'] = self.request.user.last_name
        return initial


class EditAccountAPIView(AbstractAuthedIndigoView, DetailView):
    context_object_name = 'user'
    template_name = 'indigo_app/user_account/api.html'

    def get_object(self, queryset=None):
        return self.request.user

    def post(self, request):
        request.user.editor.api_token().delete()
        # force a new one to be created
        request.user.editor.api_token()
        return self.get(request)


class AcceptTermsView(AbstractAuthedIndigoView, UpdateView):
    context_object_name = 'editor'
    template_name = 'indigo_app/user_account/accept_terms.html'
    fields = ('accepted_terms',)
    must_accept_terms = False

    def get_object(self, queryset=None):
        return self.request.user.editor

    def get_success_url(self):
        return get_request_param(self.request, self.get_redirect_field_name(), settings.LOGIN_REDIRECT_URL)
