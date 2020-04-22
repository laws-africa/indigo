from django.http import HttpResponse
from django.shortcuts import get_list_or_404

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from rest_framework.decorators import action

from ..models import Document, Attachment, Work, PublicationDocument
from ..serializers import AttachmentSerializer
from ..authz import AttachmentPermissions
from .documents import DocumentResourceView
from .misc import DEFAULT_PERMS


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
    permission_classes = DEFAULT_PERMS + (AttachmentPermissions,)

    @action(detail=True, methods=['GET'])
    def download(self, request, *args, **kwargs):
        attachment = self.get_object()
        return download_attachment(attachment)

    @action(detail=True, methods=['GET'])
    def view(self, request, *args, **kwargs):
        attachment = self.get_object()
        return view_attachment(attachment)

    def filter_queryset(self, queryset):
        return queryset.filter(document=self.document).all()


class AttachmentMediaView(DocumentResourceView, APIView):
    """ This is a helper view to serve up a named attachment file via
    a document's "media/file.ext" url, which is part of the AKN standard.
    """
    permission_classes = DEFAULT_PERMS + (AttachmentPermissions,)

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
