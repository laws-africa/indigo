from django.conf import settings
from django.views.generic import DetailView, FormView, UpdateView
from django.urls import reverse
from allauth.utils import get_request_param

from indigo_app.forms import UserForm
from .base import AbstractAuthedIndigoView


class EditAccountView(AbstractAuthedIndigoView, FormView):
    template_name = 'indigo_app/user_account/edit.html'
    form_class = UserForm

    def get_success_url(self):
        return reverse('edit_account')

    def get_form_kwargs(self):
        kwargs = super(EditAccountView, self).get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        return super(EditAccountView, self).form_valid(form)


class EditAccountAPIView(AbstractAuthedIndigoView, DetailView):
    context_object_name = 'user'
    template_name = 'indigo_app/user_account/api.html'

    def get_object(self):
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

    def get_object(self):
        return self.request.user.editor

    def get_success_url(self):
        return get_request_param(self.request, self.get_redirect_field_name(), settings.LOGIN_REDIRECT_URL)
