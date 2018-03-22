from rest_framework.exceptions import MethodNotAllowed
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions
from django_filters.rest_framework import DjangoFilterBackend


from ..models import Work
from ..serializers import WorkSerializer
from ..authz import DocumentPermissions


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
        'draft': ['exact'],
    }

    def perform_destroy(self, instance):
        if not instance.draft:
            raise MethodNotAllowed('DELETE', 'DELETE not allowed for published documents, mark as draft first.')
        instance.deleted = True
        instance.save()

    def perform_update(self, serializer):
        # check permissions just before saving, to prevent users
        # without publish permissions from setting draft = False
        if not DocumentPermissions().update_allowed(self.request, serializer):
            self.permission_denied(self.request)

        super(WorkViewSet, self).perform_update(serializer)
