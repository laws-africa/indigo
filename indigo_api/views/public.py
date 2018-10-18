import re

from django.http import Http404

from rest_framework.reverse import reverse
from rest_framework import mixins, viewsets, renderers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from cobalt import FrbrUri

from ..serializers import PublishedDocumentSerializer, MediaAttachmentSerializer
from ..renderers import AkomaNtosoRenderer, PDFResponseRenderer, EPUBResponseRenderer, HTMLResponseRenderer, ZIPResponseRenderer
from ..atom import AtomRenderer, AtomFeed

from .documents import DocumentViewMixin, DocumentResourceView, SearchView
from .attachments import view_attachment_by_filename
from ..models import Attachment, Country


FORMAT_RE = re.compile('\.([a-z0-9]+)$')


class PublishedDocumentPermission(BasePermission):
    """ Published document permissions.
    """
    def has_permission(self, request, view):
        return request.user.has_perm('indigo_api.view_published_document')


class MediaViewSet(DocumentResourceView, viewsets.ModelViewSet):
    """ Attachment view for published documents, under frbr-uri/media.json
    """
    queryset = Attachment.objects
    serializer_class = MediaAttachmentSerializer
    # TODO: perms
    permission_classes = (IsAuthenticated,)

    def filter_queryset(self, queryset):
        return queryset.filter(document=self.document).all()


class PublicAPIMixin(object):
    authentication_classes = (SessionAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated, PublishedDocumentPermission)


class PublishedDocumentDetailView(DocumentViewMixin,
                                  PublicAPIMixin,
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

    serializer_class = PublishedDocumentSerializer
    # these determine what content negotiation takes place
    renderer_classes = (renderers.JSONRenderer, AtomRenderer, PDFResponseRenderer, EPUBResponseRenderer, AkomaNtosoRenderer, HTMLResponseRenderer,
                        ZIPResponseRenderer)

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
            self.parse_frbr_uri(self.kwargs['frbr_uri'])

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
        if self.component == 'media' and self.subcomponent:
            filename = self.subcomponent
            if self.format_kwarg:
                filename += '.' + self.format_kwarg
            return view_attachment_by_filename(document.id, filename)

        if self.subcomponent:
            self.element = document.get_subcomponent(self.component, self.subcomponent)
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
                # use the request URI as the basis for this document
                serializer.context['url'] = reverse(
                    'published-document-detail',
                    request=request,
                    kwargs={'frbr_uri': self.frbr_uri.expression_uri()[1:]})
                return Response(serializer.data)

            # media attachments
            if (self.component, format) == ('media', 'json'):
                view = MediaViewSet()
                view.kwargs = {'document_id': document.id}
                view.request = request
                view.document = document
                view.initial(request)
                return view.list(request)

            # the item we're interested in
            self.element = document.doc.components().get(self.component)

        if self.element is not None and format in ['xml', 'html', 'pdf', 'epub', 'zip']:
            return Response(document)

        raise Http404

    def list(self, request):
        """ Return details on many documents.
        """
        # determine the country, so we can determine the primary language
        try:
            self.country = Country.for_code(self.kwargs['frbr_uri'][1:3])
        except Country.DoesNotExist:
            raise Http404

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
            .filter(frbr_uri__istartswith=self.kwargs['frbr_uri'])\
            .filter(language__language__iso_639_2B=self.country.primary_language.code)
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

    def parse_frbr_uri(self, frbr_uri):
        FrbrUri.default_language = None
        self.frbr_uri = FrbrUri.parse(frbr_uri)

        # validate the country and set the default language
        try:
            country = Country.for_frbr_uri(self.frbr_uri)
            self.frbr_uri.default_language = country.primary_language.code
        except Country.DoesNotExist:
            raise Http404("Country %s from FRBR URI not found" % self.frbr_uri.country)

        if not self.frbr_uri.language:
            self.frbr_uri.language = self.frbr_uri.default_language


class PublishedDocumentSearchView(PublicAPIMixin, SearchView):
    """ Search published documents.
    """
    filter_fields = {
        'frbr_uri': ['exact', 'startswith'],
    }
    serializer_class = PublishedDocumentSerializer
    scope = 'works'

    def get_queryset(self):
        try:
            country = Country.for_code(self.kwargs['country'])
        except Country.DoesNotExist:
            raise Http404

        queryset = super(PublishedDocumentSearchView, self).get_queryset()
        return queryset.published().filter(work__country=country)
