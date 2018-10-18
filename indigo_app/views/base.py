from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.views import redirect_to_login


class IndigoJSViewMixin(object):
    """ View that inject's the appropriate Backbone view name into the template, for use by the Backbone
    view system. By default, the Backbone view name is the same name as the view's class name.
    Set `js_view` to another name to change it, or the empty string to disable completely.
    """
    js_view = None

    def get_context_data(self, **kwargs):
        context = super(IndigoJSViewMixin, self).get_context_data(**kwargs)
        context['js_view'] = self.get_js_view()
        return context

    def get_js_view(self):
        if self.js_view is None:
            return self.__class__.__name__
        return self.js_view


class AbstractAuthedIndigoView(PermissionRequiredMixin, IndigoJSViewMixin):
    """ Abstract view for authenticated Indigo views.
    """
    # permissions
    raise_exception = True
    permission_required = ()
    must_accept_terms = True
    check_country_perms = True

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())

        if not self.has_permission():
            return self.handle_no_permission()

        if self.must_accept_terms and not request.user.editor.accepted_terms:
            # user must accept terms
            return redirect_to_login(self.request.get_full_path(), 'accept_terms', self.get_redirect_field_name())

        return super(AbstractAuthedIndigoView, self).dispatch(request, *args, **kwargs)

    def has_permission(self):
        return super(AbstractAuthedIndigoView, self).has_permission() and self.has_country_permission()

    def has_country_permission(self):
        if not self.check_country_perms:
            return True

        if self.request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return True

        country = self.get_country()
        if not country:
            raise Exception("This request will change state and country permissions are required, but get_country returned None.")

        return self.request.user.editor.has_country_permission(country)
