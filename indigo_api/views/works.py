from rest_framework.exceptions import MethodNotAllowed
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.generics import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend


from ..models import Work, Amendment
from ..serializers import WorkSerializer, WorkAmendmentSerializer
from ..authz import DocumentPermissions


class WorkResourceView(object):
    """ Helper mixin for views that hang off of a work URL.
    """
    def initial(self, request, **kwargs):
        self.work = self.lookup_work()
        super(WorkResourceView, self).initial(request, **kwargs)

    def lookup_work(self):
        qs = Work.objects.undeleted()
        work_id = self.kwargs['work_id']
        return get_object_or_404(qs, id=work_id)

    def get_serializer_context(self):
        context = super(WorkResourceView, self).get_serializer_context()
        context['work'] = self.work
        return context


class WorkViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Documents to be viewed or edited.
    """
    queryset = Work.objects.undeleted()
    serializer_class = WorkSerializer
    # TODO permissions on creating and publishing works
    permission_classes = (DjangoModelPermissions,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = {
        'frbr_uri': ['exact', 'startswith'],
        'country': ['exact'],
    }

    def perform_destroy(self, instance):
        if not instance.can_delete():
            raise MethodNotAllowed('DELETE', 'DELETE not allowed for works with attached documents, delete documents first.')
        instance.deleted = True
        instance.save()

    def perform_update(self, serializer):
        # check permissions just before saving, to prevent users
        # without publish permissions from setting draft = False
        if not DocumentPermissions().update_allowed(self.request, serializer):
            self.permission_denied(self.request)

        super(WorkViewSet, self).perform_update(serializer)


class WorkAmendmentViewSet(WorkResourceView, viewsets.ModelViewSet):
    queryset = Amendment.objects
    serializer_class = WorkAmendmentSerializer
    permission_classes = (DjangoModelPermissions,)

    def filter_queryset(self, queryset):
        return queryset.filter(amended_work=self.work).all()
