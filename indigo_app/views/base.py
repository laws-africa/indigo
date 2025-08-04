import asyncio

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.template.response import TemplateResponse
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.http import Http404

from indigo_api.authz import is_maintenance_mode
from indigo_api.models import Country, Work, AllPlace


class IndigoJSViewMixin(object):
    """ View that inject's the appropriate Backbone view name into the template, for use by the Backbone
    view system. By default, the Backbone view name is the same name as the view's class name.
    Set `js_view` to another name to change it, or the empty string to disable completely.
    """
    js_view = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['js_view'] = self.get_js_view()
        return context

    def get_js_view(self):
        if self.js_view is None:
            return self.__class__.__name__
        return self.js_view


class AsyncDispatchMixin:
    """ This mixin helps makes class-based async-friendly when dispatch() performs database access. This is common
    for most Indigo views since they use AbstractAuthedIndigoView. This mixin will ensure that the dispatch method
    works correctly for async views.

    The get/post method on the view must be async, and the dispatch method will call them accordingly.
    """

    # disabled atomic requests
    @transaction.non_atomic_requests
    async def dispatch(self, request, *args, **kwargs):
        # when dispatch calls the actual view, it will get back a coroutine result
        resp = await sync_to_async(super().dispatch)(request, *args, **kwargs)
        # now wait on the coroutine result
        if asyncio.iscoroutine(resp):
            return await resp
        return resp


class AbstractAuthedIndigoView(PermissionRequiredMixin, IndigoJSViewMixin):
    """ Abstract view for (potentially) authenticated Indigo views.

    Any Indigo view that may need authentication, must inherit from this view.
    Authentication is required if:

    * `authentication_required` is True
    * `permission_required` is not empty
    """
    raise_exception = True
    authentication_required = True
    permission_required = ()
    must_accept_terms = True

    def dispatch(self, request, *args, **kwargs):
        if is_maintenance_mode(request):
            return self.maintenance_response(request)

        if self.requires_authentication():
            if not request.user.is_authenticated:
                if request.htmx:
                    # don't redirect HTMX requests
                    raise PermissionDenied()
                return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())

        if request.user.is_authenticated and self.must_accept_terms and not request.user.editor.accepted_terms:
            # user must accept terms
            return redirect_to_login(self.request.get_full_path(), 'accept_terms', self.get_redirect_field_name())

        return super().dispatch(request, *args, **kwargs)

    def requires_authentication(self):
        return self.authentication_required or self.permission_required

    def maintenance_response(self, request):
        return TemplateResponse(request, "indigo_app/maintenance.html", status=503)


class PlaceViewBase(AbstractAuthedIndigoView):
    """ Views that are tied to a place, either a Country or a Locality.
    This should be the first parent class for views with multiple parents.

    The place is determined and set on the view right at the start of dispatch,
    and `country`, `locality` and `place` set accordingly.

    If the allow_all_place attribute is set to True, the view will allow the special
    'all' place, which is a special case that means all places in the system.
    """
    country = None
    locality = None
    place = None
    permission_required = ('indigo_api.view_country',)
    allow_all_place = False

    def dispatch(self, request, *args, **kwargs):
        self.determine_place()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['locality'] = self.locality
        kwargs['country'] = self.country
        kwargs['place'] = self.place
        kwargs['user_can_change_place_settings'] = self.request.user.has_perm('indigo_api.change_placesettings')
        return super().get_context_data(**kwargs)

    def determine_place(self):
        if self.kwargs['place'] == 'all' and self.allow_all_place:
            self.country = AllPlace()
        else:
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

    def has_permission(self):
        return super().has_permission() and self.has_country_permission()

    def has_country_permission(self):
        if self.request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return True

        if not self.country:
            raise Exception("This request will change state and country permissions are required, "
                            "but self.country is None.")

        if self.country.place_code == 'all':
            return self.has_all_country_permission()

        return self.request.user.editor.has_country_permission(self.country)

    def doctypes(self):
        doctypes = settings.INDIGO['DOCTYPES']
        extras = settings.INDIGO['EXTRA_DOCTYPES'].get(self.country.code)

        if extras:
            return doctypes + extras

        return doctypes

    def has_all_country_permission(self):
        return False


class PlaceWorksViewBase(PlaceViewBase):
    """Base view for views that display a list of works for a place, that adds support
    for filtering by the special All place."""
    queryset = Work.objects.order_by('-created_at').prefetch_related('country', 'locality')

    def get_base_queryset(self):
        queryset = self.queryset
        if self.country.place_code == "all":
            queryset = AllPlace.filter_works_queryset(queryset, self.request.user)
        else:
            queryset = queryset.filter(country=self.country, locality=self.locality)
        return queryset
