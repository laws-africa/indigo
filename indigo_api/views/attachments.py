from django.http import HttpResponse
from django.shortcuts import get_list_or_404
from django.utils.http import content_disposition_header

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from rest_framework.decorators import action

from ..models import Document, DocumentEditLease, Attachment, Work, PublicationDocument
from ..exceptions import DocumentChanged, EditLeaseLost
from ..serializers import AttachmentSerializer
from ..authz import ModelPermissions, RelatedDocumentPermissions
from .documents import DocumentResourceView
from .misc import DEFAULT_PERMS
from indigo.view_mixins import AtomicWriteViewSetMixin
from docpipe.soffice import soffice_convert
import os

DOC_MIMETYPES = [
    "application/vnd.oasis.opendocument.text",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/rtf",
    "text/rtf",
]


def view_attachment(attachment):
    response = HttpResponse(attachment.file.read(), content_type=attachment.mime_type)
    response['Content-Disposition'] = content_disposition_header(False, attachment.filename)
    response['Content-Length'] = str(attachment.size)
    return response


def view_attachment_by_filename(doc_id, filename):
    """ This is a helper view to serve up a named attachment file via
    a "media/file.ext" url, which is part of the AKN standard.
    """
    qs = Document.objects.undeleted().no_xml()
    document = get_object_or_404(qs, deleted__exact=False, id=doc_id)
    attachment = get_list_or_404(Attachment.objects, document=document, filename=filename)[0]
    return view_attachment(attachment)


def view_attachment_as_pdf(attachment):
    suffix = os.path.splitext(attachment.filename)[1].lstrip('.')
    pdf = soffice_convert(attachment.file, suffix, 'pdf')[0]
    file_bytes = pdf.read()
    response = HttpResponse(file_bytes, content_type="application/pdf")
    response['Content-Disposition'] = content_disposition_header(False, attachment.filename)
    response['Content-Length'] = str(len(file_bytes))
    return response


def download_attachment(attachment):
    response = view_attachment(attachment)
    response['Content-Disposition'] = content_disposition_header(True, attachment.filename)
    return response


class AttachmentViewSet(AtomicWriteViewSetMixin, DocumentResourceView, viewsets.ModelViewSet):
    queryset = Attachment.objects
    serializer_class = AttachmentSerializer
    permission_classes = DEFAULT_PERMS + (ModelPermissions, RelatedDocumentPermissions)

    @action(detail=True, methods=['GET'])
    def download(self, request, *args, **kwargs):
        attachment = self.get_object()
        return download_attachment(attachment)

    @action(detail=True, methods=['GET'])
    def view(self, request, *args, **kwargs):
        attachment = self.get_object()
        if attachment.mime_type in DOC_MIMETYPES:
            return view_attachment_as_pdf(attachment)
        return view_attachment(attachment)

    def filter_queryset(self, queryset):
        return queryset.filter(document=self.document).all()

    def check_edit_lease(self):
        token = self.request.headers.get('X-Edit-Lease-Token')
        expected_updated_at = self.request.headers.get('X-Expected-Updated-At')
        # Preserve compatibility for non-editor API clients. The Indigo editor
        # always supplies both headers for attachment mutations.
        if not token and not expected_updated_at:
            return
        if not token or not expected_updated_at:
            raise serializers.ValidationError('Both edit lease headers are required.')

        token = serializers.UUIDField().run_validation(token)
        expected_updated_at = serializers.DateTimeField().run_validation(expected_updated_at)
        document = Document.objects.select_for_update().get(pk=self.document.pk)
        if expected_updated_at != document.updated_at:
            raise DocumentChanged(document, expected_updated_at)
        try:
            lease = DocumentEditLease.objects.get(
                document=document,
                user=self.request.user,
                token=token,
                expires_at__gt=timezone.now(),
                document_updated_at=expected_updated_at,
            )
        except DocumentEditLease.DoesNotExist:
            raise EditLeaseLost()
        return lease

    def perform_create(self, serializer):
        self.check_edit_lease()
        return super().perform_create(serializer)

    def perform_update(self, serializer):
        self.check_edit_lease()
        return super().perform_update(serializer)

    def perform_destroy(self, instance):
        self.check_edit_lease()
        return super().perform_destroy(instance)


class AttachmentMediaView(DocumentResourceView, APIView):
    """ This is a helper view to serve up a named attachment file via
    a document's "media/file.ext" url, which is part of the AKN standard.
    """
    def get(self, request, document_id, filename):
        return view_attachment_by_filename(document_id, filename)


def pub_attachment_media_view(request, *args, **kwargs):
    """ copied from attachment_media_view()
    """
    frbr_uri = kwargs['frbr_uri']
    filename = kwargs['filename']
    work = Work.objects.get(frbr_uri=frbr_uri)
    attachment = get_object_or_404(PublicationDocument.objects, work=work, filename=filename)
    return view_attachment(attachment)
