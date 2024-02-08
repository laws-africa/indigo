from django.conf import settings
from django.views.generic import DetailView, UpdateView
from django.urls import reverse
from django.shortcuts import redirect
from allauth.utils import get_request_param

from indigo_app.forms import UserEditorForm
from indigo_app.models import Editor
from .base import AbstractAuthedIndigoView

def set_language_cookie(response, lang_code):
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME, lang_code,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
        secure=settings.LANGUAGE_COOKIE_SECURE,
        httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )


class EditAccountView(AbstractAuthedIndigoView, UpdateView):
    authentication_required = True
    model = Editor
    template_name = 'indigo_app/user_account/edit.html'
    form_class = UserEditorForm
    check_country_perms = False
    use_indigo_perm_required = False

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

    def form_valid(self, form):
        resp = super().form_valid(form)
        set_language_cookie(resp, form.cleaned_data['language'])
        return resp


class EditAccountAPIView(AbstractAuthedIndigoView, DetailView):
    authentication_required = True
    context_object_name = 'user'
    template_name = 'indigo_app/user_account/api.html'
    check_country_perms = False
    use_indigo_perm_required = False

    def get_object(self, queryset=None):
        return self.request.user

    def post(self, request):
        request.user.editor.api_token().delete()
        # force a new one to be created
        request.user.editor.api_token()
        return redirect('edit_account_api')


class AcceptTermsView(AbstractAuthedIndigoView, UpdateView):
    authentication_required = True
    context_object_name = 'editor'
    template_name = 'indigo_app/user_account/accept_terms.html'
    fields = ('accepted_terms',)
    must_accept_terms = False
    check_country_perms = False
    use_indigo_perm_required = False

    # TODO: check if terms accepted and redirect if so

    def get_object(self, queryset=None):
        return self.request.user.editor

    def get_success_url(self):
        return get_request_param(self.request, self.get_redirect_field_name(), settings.LOGIN_REDIRECT_URL)
