import re
import logging

from django.http import Http404, HttpResponse
from django.views.decorators.cache import cache_control
from django.shortcuts import get_list_or_404
from django.db.models import F
from django.contrib.postgres.search import SearchQuery

from rest_framework.exceptions import ValidationError, MethodNotAllowed
from rest_framework.views import APIView
from rest_framework.reverse import reverse
from rest_framework import mixins, viewsets, renderers, status
from rest_framework.generics import get_object_or_404, ListAPIView
from rest_framework.response import Response
from rest_framework.decorators import detail_route, permission_classes, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from reversion import revisions as reversion
from reversion.models import Version
from django_filters.rest_framework import DjangoFilterBackend

import lxml.html.diff
from lxml.etree import LxmlError

from .models import Document, Attachment, Annotation, DocumentActivity, Work
from .serializers import DocumentSerializer, RenderSerializer, ParseSerializer, AttachmentSerializer, DocumentAPISerializer, RevisionSerializer, AnnotationSerializer, DocumentActivitySerializer, WorkSerializer
from .renderers import AkomaNtosoRenderer, PDFResponseRenderer, EPUBResponseRenderer, HTMLResponseRenderer, ZIPResponseRenderer
from .atom import AtomRenderer, AtomFeed
from .slaw import Importer, Slaw
from .authz import DocumentPermissions, AnnotationPermissions
from .analysis import ActRefFinder
from .utils import Headline, SearchPagination, SearchRankCD
from cobalt import FrbrUri
import newrelic.agent

log = logging.getLogger(__name__)

FORMAT_RE = re.compile('\.([a-z0-9]+)$')


# Default document fields that can be use to filter list views
DOCUMENT_FILTER_FIELDS = {
    'frbr_uri': ['exact', 'startswith'],
    'country': ['exact'],
    'language': ['exact'],
    'draft': ['exact'],
    'stub': ['exact'],
    'expression_date': ['exact', 'lte', 'gte'],
}

WORK_FILTER_FIELDS = {
    'frbr_uri': ['exact', 'startswith'],
    'country': ['exact'],
    'draft': ['exact'],
}


def ping(request):
    newrelic.agent.ignore_transaction()
    return HttpResponse("pong", content_type="text/plain")


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


class DocumentViewMixin(object):
    queryset = Document.objects.undeleted().no_xml().prefetch_related('tags', 'created_by_user', 'updated_by_user')

    def initial(self, request, **kwargs):
        super(DocumentViewMixin, self).initial(request, **kwargs)

        # some of our renderers want to bypass the serializer, so that we get access to the
        # raw data objects
        if getattr(self.request.accepted_renderer, 'serializer_class', None):
            self.serializer_class = self.request.accepted_renderer.serializer_class

    def table_of_contents(self, document, uri=None):
        # this updates the TOC entries by adding a 'url' component
        # based on the document's URI and the path of the TOC subcomponent
        uri = uri or document.doc.frbr_uri
        toc = document.table_of_contents()

        def add_url(item):
            uri.expression_component = item['component']
            uri.expression_subcomponent = item.get('subcomponent')

            item['url'] = reverse(
                'published-document-detail',
                request=self.request,
                kwargs={'frbr_uri': uri.expression_uri()[1:]})

            for kid in item.get('children', []):
                add_url(kid)

        for item in toc:
            add_url(item)

        return toc


# Read/write REST API
class DocumentViewSet(DocumentViewMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Documents to be viewed or edited.
    """
    serializer_class = DocumentSerializer
    permission_classes = (DjangoModelPermissions, DocumentPermissions)
    renderer_classes = (renderers.JSONRenderer, PDFResponseRenderer, EPUBResponseRenderer,
                        HTMLResponseRenderer, AkomaNtosoRenderer, ZIPResponseRenderer,
                        renderers.BrowsableAPIRenderer)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = DOCUMENT_FILTER_FIELDS

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

        super(DocumentViewSet, self).perform_update(serializer)

    @detail_route(methods=['GET', 'PUT'])
    def content(self, request, *args, **kwargs):
        """ This exposes a GET and PUT resource at ``/api/documents/1/content`` which allows
        the content of the document to be fetched and set independently of the metadata. This
        is useful because the content can be large.
        """
        instance = self.get_object()

        if request.method == 'GET':
            return Response({'content': self.get_object().document_xml})

        if request.method == 'PUT':
            try:
                instance.reset_xml(request.data.get('content'))
                instance.save_with_revision(request.user)
            except LxmlError as e:
                raise ValidationError({'content': ["Invalid XML: %s" % e.message]})

            return Response({'content': instance.document_xml})

    @detail_route(methods=['GET'])
    def toc(self, request, *args, **kwargs):
        """ This exposes a GET resource at ``/api/documents/1/toc`` which gives
        a table of contents for the document.
        """
        return Response({'toc': self.table_of_contents(self.get_object())})


class DocumentResourceView(object):
    """ Helper mixin for views that hang off of a document URL.

    Includes enforcing permissions based on the document, not the resource.
    """
    def initial(self, request, **kwargs):
        self.document = self.lookup_document()
        super(DocumentResourceView, self).initial(request, **kwargs)

    def lookup_document(self):
        qs = Document.objects.undeleted().no_xml()
        doc_id = self.kwargs['document_id']
        return get_object_or_404(qs, id=doc_id)

    def get_serializer_context(self):
        context = super(DocumentResourceView, self).get_serializer_context()
        context['document'] = self.document
        return context


class AttachmentViewSet(DocumentResourceView, viewsets.ModelViewSet):
    queryset = Attachment.objects
    serializer_class = AttachmentSerializer
    permission_classes = (IsAuthenticated,)

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
    a "media/file.ext" url, which is part of the AKN standard.
    """
    doc_id = kwargs['document_id']
    filename = kwargs['filename']
    return view_attachment_by_filename(doc_id, filename)


class AnnotationViewSet(DocumentResourceView, viewsets.ModelViewSet):
    queryset = Annotation.objects
    serializer_class = AnnotationSerializer
    permission_classes = (IsAuthenticated, AnnotationPermissions)

    def filter_queryset(self, queryset):
        return queryset.filter(document=self.document).all()


class RevisionViewSet(DocumentResourceView, viewsets.ReadOnlyModelViewSet):
    serializer_class = RevisionSerializer
    permission_classes = (IsAuthenticated,)

    @detail_route(methods=['POST'])
    def restore(self, request, *args, **kwargs):
        # check permissions on the OLD object
        if not DocumentPermissions().has_object_permission(request, self, self.document):
            self.permission_denied(self.request)

        revision = self.get_object()

        # check permissions on the NEW object
        version = revision.version_set.all()[0]
        document = version.object_version.object
        if not DocumentPermissions().has_object_permission(request, self, document):
            self.permission_denied(self.request)

        with reversion.create_revision():
            reversion.set_user(request.user)
            reversion.set_comment("Restored revision %s" % revision.id)
            revision.revert()

        return Response(status=200)

    @detail_route(methods=['GET'])
    @cache_control(public=True, max_age=24 * 3600)
    def diff(self, request, *args, **kwargs):
        # this can be cached because the underlying data won't change (although
        # the formatting might)
        revision = self.get_object()
        version = revision.version_set.all()[0]

        # most recent version just before this one
        old_version = Version.objects\
            .filter(content_type=version.content_type)\
            .filter(object_id_int=version.object_id_int)\
            .filter(id__lt=version.id)\
            .order_by('-id')\
            .first()

        if old_version:
            old_html = old_version.object_version.object.to_html()
        else:
            old_html = ""
        new_html = version.object_version.object.to_html()
        diff = lxml.html.diff.htmldiff(old_html, new_html)

        # TODO: include other diff'd attributes

        return Response({'content': diff})

    def get_queryset(self):
        return self.document.revisions()


class DocumentActivityViewSet(DocumentResourceView,
                              mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              viewsets.GenericViewSet):
    """ API endpoint to see who's working in a document.
    """
    serializer_class = DocumentActivitySerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.document.activities.prefetch_related('user').all()

    def list(self, request, *args, **kwargs):
        # clean up old activity
        DocumentActivity.vacuum(self.document)
        return super(DocumentActivityViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # does it already exist?
        activity = None

        # update activity if we have a nonce
        if request.data['nonce']:
            activity = self.get_queryset().filter(user=request.user, nonce=request.data['nonce']).first()

        if activity:
            activity.touch()
            activity.save()
        else:
            # new activity
            super(DocumentActivityViewSet, self).create(request, *args, **kwargs)

        return self.list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        activity = self.get_queryset().filter(user=request.user, nonce=request.data['nonce']).first()
        if activity:
            activity.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublishedDocumentDetailView(DocumentViewMixin,
                                  mixins.RetrieveModelMixin,
                                  mixins.ListModelMixin,
                                  viewsets.GenericViewSet):
    """
    The public read-only API for viewing and listing published documents by FRBR URI.

    This handles both listing many documents based on a URI prefix, and
    returning details for a single document. The default content type
    is JSON.

    For example:

    * ``/za/``: list all published documents for South Africa.
    * ``/za/act/1994/2/``: one document, Act 2 of 1992
    * ``/za/act/1994/summary.atom``: all the acts from 1994 as an atom feed
    * ``/za/act/1994.pdf``: all the acts from 1994 as a PDF
    * ``/za/act/1994.epub``: all the acts from 1994 as an ePUB

    """

    # only published documents
    queryset = DocumentViewMixin.queryset.published()

    serializer_class = DocumentSerializer
    pagination_class = PageNumberPagination
    # these determine what content negotiation takes place
    renderer_classes = (renderers.JSONRenderer, AtomRenderer, PDFResponseRenderer, EPUBResponseRenderer, AkomaNtosoRenderer, HTMLResponseRenderer,
                        ZIPResponseRenderer)
    permission_classes = (AllowAny,)

    def initial(self, request, **kwargs):
        super(PublishedDocumentDetailView, self).initial(request, **kwargs)
        # ensure the URI starts with a slash
        self.kwargs['frbr_uri'] = '/' + self.kwargs['frbr_uri']

    def perform_content_negotiation(self, request, force=False):
        # force content negotiation to succeed, because sometimes the suffix format
        # doesn't match a renderer
        return super(PublishedDocumentDetailView, self).perform_content_negotiation(request, force=True)

    def get(self, request, **kwargs):
        # try parse it as an FRBR URI, if that succeeds, we'll lookup the document
        # that document matches, otherwise we'll assume they're trying to
        # list documents with a prefix URI match.
        try:
            self.frbr_uri = FrbrUri.parse(self.kwargs['frbr_uri'])

            # ensure we haven't mistaken '/za-cpt/act/by-law/2011/full.atom' for a URI
            if self.frbr_uri.number in ['full', 'summary'] and self.format_kwarg == 'atom':
                raise ValueError()

            # in a URL like
            #
            #   /act/1980/1/toc
            #
            # don't mistake 'toc' for a language, it's really equivalent to
            #
            #   /act/1980/1/eng/toc
            #
            # if eng is the default language.
            if self.frbr_uri.language == 'toc':
                self.frbr_uri.language = self.frbr_uri.default_language
                self.frbr_uri.expression_component = 'toc'

            return self.retrieve(request)
        except ValueError:
            return self.list(request)

    def retrieve(self, request, *args, **kwargs):
        """ Return details on a single document, possible only part of that document.
        """
        # these are made available to the renderer
        self.component = self.frbr_uri.expression_component or 'main'
        self.subcomponent = self.frbr_uri.expression_subcomponent
        format = self.request.accepted_renderer.format
        # Tell the renderer that published documents shouldn't include stub content
        self.no_stub_content = True

        # get the document
        document = self.get_object()

        # asking for a media attachment?
        if self.component == 'media':
            filename = self.subcomponent
            if self.format_kwarg:
                filename += '.' + self.format_kwarg
            return view_attachment_by_filename(document.id, filename)

        if self.subcomponent:
            self.element = document.doc.get_subcomponent(self.component, self.subcomponent)
        else:
            # special cases of the entire document

            # table of contents
            if (self.component, format) == ('toc', 'json'):
                uri = document.doc.frbr_uri
                uri.expression_date = self.frbr_uri.expression_date
                return Response({'toc': self.table_of_contents(document, uri)})

            # json description
            if (self.component, format) == ('main', 'json'):
                serializer = self.get_serializer(document)
                return Response(serializer.data)

            # the item we're interested in
            self.element = document.doc.components().get(self.component)

        if self.element is not None and format in ['xml', 'html', 'pdf', 'epub', 'zip']:
            return Response(document)

        raise Http404

    def list(self, request):
        """ Return details on many documents.
        """
        if self.request.accepted_renderer.format == 'atom':
            # feeds show most recently changed first
            self.queryset = self.queryset.order_by('-updated_at')

            # what type of feed?
            if self.kwargs['frbr_uri'].endswith('summary'):
                self.kwargs['feed'] = 'summary'
                self.kwargs['frbr_uri'] = self.kwargs['frbr_uri'][:-7]
            elif self.kwargs['frbr_uri'].endswith('full'):
                self.kwargs['feed'] = 'full'
                self.kwargs['frbr_uri'] = self.kwargs['frbr_uri'][:-4]
            else:
                raise Http404

            if self.kwargs['feed'] == 'full':
                # full feed is big, limit it
                self.paginator.page_size = AtomFeed.full_feed_page_size

        elif self.request.accepted_renderer.format in ['pdf', 'epub', 'zip']:
            # NB: don't try to sort in the db, that's already sorting to
            # return the latest expression of each doc. Sort here instead.
            documents = sorted(self.filter_queryset(self.get_queryset()).all(), key=lambda d: d.title)
            # bypass pagination and serialization
            return Response(documents)

        elif self.format_kwarg and self.format_kwarg != "json":
            # they explicitly asked for something other than JSON,
            # but listing views don't support that, so 404
            raise Http404

        else:
            # either explicitly or implicitly json
            self.request.accepted_renderer = renderers.JSONRenderer()
            self.request.accepted_media_type = self.request.accepted_renderer.media_type
            self.serializer_class = PublishedDocumentDetailView.serializer_class

        response = super(PublishedDocumentDetailView, self).list(request)

        # add alternate links for json
        if self.request.accepted_renderer.format == 'json':
            self.add_alternate_links(response, request)

        return response

    def add_alternate_links(self, response, request):
        url = reverse('published-document-detail', request=request,
                      kwargs={'frbr_uri': self.kwargs['frbr_uri'][1:]})

        if url.endswith('/'):
            url = url[:-1]

        response.data['links'] = [
            {
                "rel": "alternate",
                "title": AtomFeed.summary_feed_title,
                "href": url + "/summary.atom",
                "mediaType": AtomRenderer.media_type,
            },
            {
                "rel": "alternate",
                "title": AtomFeed.full_feed_title,
                "href": url + "/full.atom",
                "mediaType": AtomRenderer.media_type,
            },
            {
                "rel": "alternate",
                "title": "PDF",
                "href": url + ".pdf",
                "mediaType": "application/pdf"
            },
            {
                "rel": "alternate",
                "title": "ePUB",
                "href": url + ".epub",
                "mediaType": "application/epub+zip"
            },
        ]

    def get_object(self):
        """ Find and return one document, used by retrieve()
        """
        try:
            obj = self.get_queryset().get_for_frbr_uri(self.frbr_uri)
            if not obj:
                raise ValueError()
        except ValueError as e:
            raise Http404(e.message)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj

    def filter_queryset(self, queryset):
        """ Filter the queryset, used by list()
        """
        queryset = queryset\
            .latest_expression()\
            .filter(frbr_uri__istartswith=self.kwargs['frbr_uri'])
        if queryset.count() == 0:
            raise Http404
        return queryset

    def get_format_suffix(self, **kwargs):
        """ Used during content negotiation.
        """
        match = FORMAT_RE.search(self.kwargs['frbr_uri'])
        if match:
            # strip it from the uri
            self.kwargs['frbr_uri'] = self.kwargs['frbr_uri'][0:match.start()]
            return match.group(1)

    def handle_exception(self, exc):
        # Formats like atom and XML don't render exceptions well, so just
        # fall back to HTML
        if hasattr(self.request, 'accepted_renderer') and self.request.accepted_renderer.format in ['xml', 'atom']:
            self.request.accepted_renderer = renderers.StaticHTMLRenderer()
            self.request.accepted_media_type = renderers.StaticHTMLRenderer.media_type

        return super(PublishedDocumentDetailView, self).handle_exception(exc)


class ParseView(APIView):
    """ Parse text into Akoma Ntoso, returning Akoma Ntoso XML.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ParseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fragment = serializer.validated_data.get('fragment')
        importer = Importer()
        importer.fragment = fragment
        importer.fragment_id_prefix = serializer.validated_data.get('id_prefix')
        importer.country = request.user.editor.country_code

        upload = self.request.data.get('file')
        if upload:
            # we got a file
            try:
                document = importer.import_from_upload(upload, self.request)
            except ValueError as e:
                log.error("Error during import: %s" % e.message, exc_info=e)
                raise ValidationError({'file': e.message or "error during import"})
        else:
            # plain text
            try:
                text = serializer.validated_data.get('content')
                document = importer.import_from_text(text, self.request)
            except ValueError as e:
                log.error("Error during import: %s" % e.message, exc_info=e)
                raise ValidationError({'content': e.message or "error during import"})

        if not document:
            raise ValidationError("Nothing to parse! Either 'file' or 'content' must be provided.")

        # output
        if fragment:
            return Response({'output': document.to_xml()})
        else:
            return Response({'output': document.document_xml})


class RenderView(APIView):
    """ Support for rendering a document on the server.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        serializer = RenderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document = DocumentSerializer().update_document(Document(), validated_data=serializer.validated_data['document'])
        # the serializer ignores the id field, but we need it for rendering
        document.id = serializer.initial_data['document'].get('id')
        return Response({'output': document.to_html()})


class LinkTermsView(APIView):
    """ Support for running term discovery and linking on a document.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = DocumentAPISerializer(data=self.request.data)
        serializer.fields['document'].fields['content'].required = True
        serializer.is_valid(raise_exception=True)
        document = serializer.fields['document'].update_document(Document(), serializer.validated_data['document'])

        self.link_terms(document)

        return Response({'document': {'content': document.document_xml}})

    def link_terms(self, doc):
        Slaw().link_terms(doc)


class LinkReferencesView(APIView):
    """ Find and link references to other documents (acts)
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = DocumentAPISerializer(data=self.request.data)
        serializer.fields['document'].fields['content'].required = True
        serializer.is_valid(raise_exception=True)
        document = serializer.fields['document'].update_document(Document(), serializer.validated_data['document'])

        self.find_references(document)

        return Response({'document': {'content': document.document_xml}})

    def find_references(self, document):
        ActRefFinder().find_references_in_document(document)


class SearchView(DocumentViewMixin, ListAPIView):
    """ Search!
    """
    serializer_class = DocumentSerializer
    pagination_class = SearchPagination
    filter_backends = (DjangoFilterBackend,)
    filter_fields = DOCUMENT_FILTER_FIELDS
    permission_classes = (AllowAny,)

    # Search scope, either 'documents' or 'works'.
    scope = 'documents'

    def filter_queryset(self, queryset):
        query = SearchQuery(self.request.query_params.get('q'))

        queryset = super(SearchView, self).filter_queryset(queryset)
        queryset = queryset.filter(search_vector=query)

        # anonymous users can't see drafts
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(draft=False)

        if self.scope == 'works':
            # Search for distinct works, which means getting the latest
            # expression of all matching works. To do this, they must
            # be ordered by expression date, which means paginating
            # search results by rank is a problem.
            # So, get all matching expressions, then paginate by re-querying
            # by document id, and order by rank.
            doc_ids = [d.id for d in queryset.latest_expression().only('id').prefetch_related(None)]
            queryset = queryset.filter(id__in=doc_ids)

        # the most expensive part of the search is the snippet/headline generation, which
        # doesn't use the search vector. It adds about 500ms to the query. Doing it here,
        # or doing it only on the required document ids, doesn't seem to have an impact.
        queryset = queryset\
            .annotate(
                rank=SearchRankCD(F('search_vector'), query),
                snippet=Headline(F('search_text'), query, options='StartSel=<mark>, StopSel=</mark>'))\
            .order_by('-rank')

        return queryset

    def get_serializer(self, queryset, *args, **kwargs):
        serializer = super(SearchView, self).get_serializer(queryset, *args, **kwargs)

        # add _rank and _snippet to the serialized docs
        for i, doc in enumerate(queryset):
            assert doc.id == serializer.data[i]['id']
            serializer.data[i]['_rank'] = doc.rank
            serializer.data[i]['_snippet'] = doc.snippet

        return serializer


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def new_auth_token(request):
    Token.objects.filter(user=request.user).delete()
    token, _ = Token.objects.get_or_create(user=request.user)
    return Response({'auth_token': token.key})


class WorkViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Documents to be viewed or edited.
    """
    queryset = Work.objects.undeleted()
    serializer_class = WorkSerializer
    # TODO permissions on creating and publishing works
    permission_classes = (DjangoModelPermissions,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = WORK_FILTER_FIELDS

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
