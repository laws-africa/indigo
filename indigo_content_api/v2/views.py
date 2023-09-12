import re

from django.http import Http404
from rest_framework import mixins, viewsets, renderers
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.versioning import NamespaceVersioning

from cobalt import FrbrUri

from indigo_api.models import Attachment, Country, Document, TaxonomyTopic, TaxonomyVocabulary, Locality
from indigo_api.renderers import AkomaNtosoRenderer, PDFRenderer, EPUBRenderer, HTMLRenderer, ZIPRenderer
from indigo_api.views.attachments import view_attachment
from indigo_api.views.documents import DocumentViewMixin
from indigo_app.views.works import publication_document_response
from .serializers import CountrySerializer, MediaAttachmentSerializer, PublishedDocumentSerializer, \
    TaxonomyTopicSerializer, TaxonomySerializer, PublishedDocUrlMixin, PublishedDocumentCommencementsSerializer,\
    PublishedDocumentTimelineSerializer

FORMAT_RE = re.compile(r'\.([a-z0-9]+)$')


class PublishedDocumentPermission(BasePermission):
    """ Published document permissions.
    """
    def has_permission(self, request, view):
        return request.user.has_perm('indigo_api.view_published_document')


class ContentAPIBase(object):
    """ Base class for Content API views, with common settings.
    """
    authentication_classes = (SessionAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated, PublishedDocumentPermission)
    versioning_class = NamespaceVersioning


class PlaceAPIBase(ContentAPIBase):
    """ A place-based API view. Allows for place-based permissions checks.
    """
    country = None
    locality = None
    place = None

    def determine_place(self):
        self.place = self.locality or self.country

    def check_permissions(self, request):
        # ensure we have a country and locality before checking permissions
        self.determine_place()
        super(PlaceAPIBase, self).check_permissions(request)


class FrbrUriViewMixin(PlaceAPIBase):
    """ An API view that uses a frbr_uri kwarg parameter to identify a work or document.

    This parses the FRBR URI, ensures it is valid, and stores it in .frbr_uri.
    """
    def initial(self, request, **kwargs):
        # ensure the URI starts with a slash
        self.kwargs['frbr_uri'] = '/' + self.kwargs['frbr_uri']
        super(FrbrUriViewMixin, self).initial(request, **kwargs)
        self.frbr_uri = self.parse_frbr_uri(self.kwargs['frbr_uri'])

    def parse_frbr_uri(self, frbr_uri):
        FrbrUri.default_language = None
        try:
            frbr_uri = FrbrUri.parse(frbr_uri)
        except ValueError:
            return None

        frbr_uri.default_language = self.country.primary_language.code
        if not frbr_uri.language:
            frbr_uri.language = frbr_uri.default_language

        return frbr_uri

    def determine_place(self):
        parts = self.kwargs['frbr_uri'].split('/')
        # TODO: split this up into v1 and v2
        place = parts[2] if parts[1] == 'akn' else parts[1]
        try:
            self.country, self.locality = Country.get_country_locality(place)
        except (Country.DoesNotExist, Locality.DoesNotExist):
            raise Http404

        super(FrbrUriViewMixin, self).determine_place()

    def get_document(self):
        """ Find and return one document based on the FRBR URI
        """
        if not self.frbr_uri:
            raise Http404

        try:
            obj = self.get_document_queryset().get_for_frbr_uri(self.frbr_uri)
            if not obj:
                raise ValueError()
        except ValueError as e:
            raise Http404(str(e))

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj

    def get_document_queryset(self):
        return self.document_queryset


class CountryViewSet(ContentAPIBase, mixins.ListModelMixin, viewsets.GenericViewSet):
    """ List of countries that the content API supports.
    """
    queryset = Country.objects.prefetch_related('localities', 'country')
    serializer_class = CountrySerializer


class TaxonomyView(ContentAPIBase, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = TaxonomyVocabulary.objects.prefetch_related('topics')
    serializer_class = TaxonomySerializer


class TaxonomyTopicView(ContentAPIBase, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = TaxonomyTopic.get_root_nodes()
    serializer_class = TaxonomyTopicSerializer


class PublishedDocumentDetailView(DocumentViewMixin,
                                  FrbrUriViewMixin,
                                  mixins.RetrieveModelMixin,
                                  mixins.ListModelMixin,
                                  viewsets.GenericViewSet):
    """
    The public read-only API for viewing and listing published documents by FRBR URI.

    This handles both listing many documents based on a URI prefix, and
    returning details for a single document. The default content type
    is JSON.

    For example:

    * ``/akn/za/``: list all published documents for South Africa.
    * ``/akn/za/act/1994/2/``: one document, Act 2 of 1992
    * ``/akn/za/act/1994.epub``: all the acts from 1994 as an ePUB

    """

    # only published documents
    queryset = DocumentViewMixin.queryset.published()
    document_queryset = queryset

    serializer_class = PublishedDocumentSerializer
    # these determine what content negotiation takes place
    renderer_classes = (renderers.JSONRenderer, PDFRenderer, EPUBRenderer, AkomaNtosoRenderer, HTMLRenderer, ZIPRenderer)

    def perform_content_negotiation(self, request, force=False):
        # force content negotiation to succeed, because sometimes the suffix format
        # doesn't match a renderer
        return super().perform_content_negotiation(request, force=True)

    def get(self, request, **kwargs):
        if self.frbr_uri:
            return self.retrieve(request)
        else:
            return self.list(request)

    def retrieve(self, request, *args, **kwargs):
        """ Return details on a single document, possible only part of that document.
        """
        # these are made available to the renderer
        self.component = self.frbr_uri.work_component or 'main'
        self.portion = self.frbr_uri.portion
        format = self.request.accepted_renderer.format

        # get the document
        document = self.get_document()

        if self.portion:
            # get the component, if any, and then the portion within that component
            component = None
            if self.frbr_uri.work_component:
                component = document.doc.components().get(self.frbr_uri.work_component)
                if component is None:
                    raise Http404
            self.element = document.doc.get_portion_element(self.portion, component)
        else:
            # special cases of the entire document

            # json description
            if (self.component, format) == ('main', 'json'):
                serializer = self.get_serializer(document)
                # use the request URI as the basis for this document
                serializer.context['url'] = serializer.published_doc_url(
                    document, request, frbr_uri=self.frbr_uri.expression_uri()
                )
                return Response(serializer.data)

            # the item we're interested in
            self.element = document.doc.components().get(self.component)

        formats = [r.format for r in self.renderer_classes]
        if self.element is not None and format in formats:
            return Response(document)

        raise Http404

    def list(self, request):
        """ Return details on many documents.
        """
        if self.request.accepted_renderer.format in ['pdf', 'epub', 'zip']:
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
            # either explicitly or implicitly json -- reset certain settings
            self.serializer_class = self.__class__.serializer_class
            self.request.accepted_renderer = renderers.JSONRenderer()
            self.request.accepted_media_type = self.request.accepted_renderer.media_type

        response = super(PublishedDocumentDetailView, self).list(request)

        # add alternate links for json
        if self.request.accepted_renderer.format == 'json':
            self.add_alternate_links(response, request)

        return response

    def add_alternate_links(self, response, request):
        serializer = self.get_serializer(instance=None)
        url = serializer.published_doc_url(None, request, frbr_uri=self.kwargs['frbr_uri'])

        if url.endswith('/'):
            url = url[:-1]

        response.data['links'] = [
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

    def filter_queryset(self, queryset):
        """ Filter the queryset, used by list()
        """
        queryset = super(PublishedDocumentDetailView, self).filter_queryset(queryset)
        queryset = queryset\
            .latest_expression()\
            .filter(frbr_uri__istartswith=self.kwargs['frbr_uri'])\
            .filter(language__language__iso_639_2T=self.country.primary_language.code)
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
        # Formats like XML don't render exceptions well, so just
        # fall back to HTML
        if hasattr(self.request, 'accepted_renderer') and self.request.accepted_renderer.format in ['xml']:
            self.request.accepted_renderer = renderers.StaticHTMLRenderer()
            self.request.accepted_media_type = renderers.StaticHTMLRenderer.media_type

        return super(PublishedDocumentDetailView, self).handle_exception(exc)


class PublishedDocumentCommencementsView(PublishedDocumentDetailView):
    serializer_class = PublishedDocumentCommencementsSerializer
    renderer_classes = (renderers.JSONRenderer,)


class PublishedDocumentTimelineView(PublishedDocumentCommencementsView):
    serializer_class = PublishedDocumentTimelineSerializer


class PublishedDocumentTOCView(DocumentViewMixin, FrbrUriViewMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet, PublishedDocUrlMixin):
    """ View that returns the TOC for a document.
    """
    renderer_classes = (renderers.JSONRenderer,)
    document_queryset = Document.objects \
        .undeleted() \
        .published()

    def get(self, request, **kwargs):
        document = self.get_document()
        uri = document.doc.frbr_uri
        uri.expression_date = self.frbr_uri.expression_date
        return Response({'toc': self.table_of_contents(document, uri)})

    def table_of_contents(self, document, uri=None):
        toc = super().table_of_contents(document, uri)

        # this updates the TOC entries by adding a 'url' component
        # based on the document's URI and the path of the TOC subcomponent
        uri = uri or document.doc.frbr_uri

        def add_url(item):
            uri.work_component = item['component']
            # if the item doesn't normally have an eid, use the type name as the portion, otherwise use the eid
            uri.portion = item['type'] if item['type'] in document.doc.non_eid_portions else item.get('id')
            item['url'] = self.published_doc_url(
                document, self.request, frbr_uri=uri.expression_uri()
            )

            for kid in item.get('children', []):
                add_url(kid)

        for item in toc:
            add_url(item)

        return toc


class PublishedDocumentMediaView(FrbrUriViewMixin,
                                 mixins.RetrieveModelMixin,
                                 mixins.ListModelMixin,
                                 viewsets.GenericViewSet):
    """ View to return media attached to a document or work,
    either as a list or an individual file.

    Also handles the special-cased /media/publication/publication-document.pdf
    """

    queryset = Attachment.objects
    serializer_class = MediaAttachmentSerializer
    document_queryset = Document.objects\
        .undeleted()\
        .no_xml()\
        .published()

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset).filter(document=self.get_document())

    def get_file(self, request, filename, *args, **kwargs):
        """ Download a media file.
        """
        attachment = self.filter_queryset(self.get_queryset())\
            .filter(filename=filename)\
            .first()
        if not attachment:
            raise Http404()
        return view_attachment(attachment)

    def get_publication_document(self, request, filename, *args, **kwargs):
        """ Download the media publication file for a work.
        """
        work = self.get_document().work

        if work.publication_document and work.publication_document.filename == filename:
            return publication_document_response(work.publication_document)

        raise Http404()
