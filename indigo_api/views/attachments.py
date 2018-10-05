from django.http import HttpResponse
from django.shortcuts import get_list_or_404

from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.decorators import detail_route, permission_classes, api_view
from rest_framework.permissions import IsAuthenticated

from ..models import Document, Attachment
from ..serializers import AttachmentSerializer
from ..authz import AttachmentPermissions
from .documents import DocumentResourceView


def view_attachment(attachment):
    response = HttpResponse(attachment.file.read(), content_type=attachment.mime_type)
    response['Content-Disposition'] = 'inline; filename=%s' % attachment.filename
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


def download_attachment(attachment):
    response = view_attachment(attachment)
    response['Content-Disposition'] = 'attachment; filename=%s' % attachment.filename
    return response


class AttachmentViewSet(DocumentResourceView, viewsets.ModelViewSet):
    queryset = Attachment.objects
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated, AttachmentPermissions)

    @detail_route(methods=['GET'])
    def download(self, request, *args, **kwargs):
        attachment = self.get_object()
        return download_attachment(attachment)

    @detail_route(methods=['GET'])
    def view(self, request, *args, **kwargs):
        attachment = self.get_object()
        return view_attachment(attachment)

    def filter_queryset(self, queryset):
        return queryset.filter(document=self.document).all()


@permission_classes((IsAuthenticated,))
@api_view()
def attachment_media_view(request, *args, **kwargs):
    """ This is a helper view to serve up a named attachment file via
    a document's "media/file.ext" url, which is part of the AKN standard.
    """
    doc_id = kwargs['document_id']
    filename = kwargs['filename']
    return view_attachment_by_filename(doc_id, filename)
