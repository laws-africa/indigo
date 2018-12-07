from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.http import Http404

from indigo_api.models import Country


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

    For views that accept POST, PUT, PATCH or DELETE methods, this view can optionally
    check if the user has appropriate country permissions. In that case, +check_country_perms+
    must be True and +get_country()+ must be implemented.
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

        if not hasattr(self, 'get_country'):
            raise Exception("This request will change state and country permissions are required, "
                            "but the view (%s) doesn't support get_country()" % self)

        country = self.get_country()
        if not country:
            raise Exception("This request will change state and country permissions are required, "
                            "but get_country returned None.")

        return self.request.user.editor.has_country_permission(country)


class PlaceBasedView(object):
    """ Views that are tied to a place, either a Country or a Locality.
    """
    country = None
    locality = None
    place = None

    def dispatch(self, request, *args, **kwargs):
        self.determine_place()
        return super(PlaceBasedView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['locality'] = self.locality
        kwargs['country'] = self.country
        kwargs['place'] = self.place
        return super(PlaceBasedView, self).get_context_data(**kwargs)

    def determine_place(self):
        parts = self.kwargs['place'].split('-', 1)
        country = parts[0]
        locality = parts[1] if len(parts) > 1 else None

        try:
            self.country = Country.for_code(country)
        except Country.DoesNotExist:
            raise Http404

        if locality:
            self.locality = self.country.localities.filter(code=locality).first()
            if not self.locality:
                raise Http404

        self.place = self.locality or self.country
