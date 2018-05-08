from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework import viewsets, status
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.generics import get_object_or_404
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import arrow

from ..models import Work, Amendment
from ..serializers import WorkSerializer, WorkAmendmentSerializer, DocumentSerializer
from ..authz import DocumentPermissions


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


class WorkViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Documents to be viewed or edited.
    """
    queryset = Work.objects
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
            raise MethodNotAllowed('DELETE', 'DELETE not allowed for works with related works or documents, unlink documents and works first.')
        return super(WorkViewSet, self).perform_destroy(instance)

    def perform_update(self, serializer):
        # check permissions just before saving, to prevent users
        # without publish permissions from setting draft = False
        if not DocumentPermissions().update_allowed(self.request, serializer):
            self.permission_denied(self.request)

        super(WorkViewSet, self).perform_update(serializer)

    @detail_route(methods=['POST'])
    def expressions_at(self, request, *args, **kwargs):
        """ Create a new document at exactly this expression date.
        """
        date = request.GET.get('date')
        if not date:
            raise ValidationError({'date': 'A valid date parameter must be provided.'})
        try:
            date = arrow.get(date).date()
        except arrow.parser.ParserError:
            raise ValidationError({'date': 'A valid date parameter must be provided.'})

        work = self.get_object()
        doc = work.create_expression_at(date)

        serializer = DocumentSerializer(context={'request': request}, instance=doc)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class WorkAmendmentViewSet(WorkResourceView, viewsets.ModelViewSet):
    queryset = Amendment.objects.prefetch_related('amending_work', 'created_by_user', 'updated_by_user')
    serializer_class = WorkAmendmentSerializer
    permission_classes = (DjangoModelPermissions,)

    def filter_queryset(self, queryset):
        return queryset.filter(amended_work=self.work).all()
