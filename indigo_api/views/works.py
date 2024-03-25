from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.generics import get_object_or_404
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters

from ..models import Work, Amendment
from ..serializers import WorkSerializer, WorkAmendmentSerializer


class WorkResourceView(object):
    """ Helper mixin for views that hang off of a work URL.
    """
    def initial(self, request, **kwargs):
        self.work = self.lookup_work()
        super(WorkResourceView, self).initial(request, **kwargs)

    def lookup_work(self):
        qs = Work.objects
        work_id = self.kwargs['work_id']
        return get_object_or_404(qs, id=work_id)

    def get_serializer_context(self):
        context = super(WorkResourceView, self).get_serializer_context()
        context['work'] = self.work
        return context


class WorkFilterSet(filters.FilterSet):
    country = filters.CharFilter(method='country_filter')

    class Meta:
        model = Work
        fields = {
            'frbr_uri': ['exact', 'startswith'],
        }

    def country_filter(self, queryset, name, value):
        return queryset.filter(country__country__iso=value.upper())


class WorkViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Documents to be viewed or edited.
    """
    queryset = Work.objects.order_by('frbr_uri').prefetch_related('parent_work', 'repealed_by')
    serializer_class = WorkSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter)
    filterset_class = WorkFilterSet
    search_fields = ('title', 'frbr_uri')


class WorkAmendmentViewSet(WorkResourceView, viewsets.ReadOnlyModelViewSet):
    queryset = Amendment.objects.prefetch_related('amending_work', 'created_by_user', 'updated_by_user')
    serializer_class = WorkAmendmentSerializer
    permission_classes = (DjangoModelPermissions,)

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset).filter(amended_work=self.work).all()
