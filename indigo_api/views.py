import re
import logging

import arrow
from django.http import Http404, HttpResponse
from django.template.loader import find_template, render_to_string, TemplateDoesNotExist

from rest_framework.exceptions import ValidationError, MethodNotAllowed
from rest_framework.views import APIView
from rest_framework.reverse import reverse
from rest_framework import mixins, viewsets, renderers
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly, AllowAny

import lxml.etree as ET
from lxml.etree import LxmlError

from .models import Document, Attachment
from .serializers import DocumentSerializer, AkomaNtosoRenderer, ConvertSerializer, AttachmentSerializer, LinkTermsSerializer
from .slaw import Importer, Slaw
from cobalt import FrbrUri
from cobalt.render import HTMLRenderer

log = logging.getLogger(__name__)

FORMAT_RE = re.compile('\.([a-z0-9]+)$')


def view_attachment(attachment):
    response = HttpResponse(attachment.file.read(), content_type=attachment.mime_type)
    response['Content-Length'] = str(attachment.size)
    return response


def download_attachment(attachment):
    response = view_attachment(attachment)
    response['Content-Disposition'] = 'attachment; filename=%s' % attachment.filename
    return response


def document_to_html(document, coverpage=True):
    """ Render an entire document to HTML.

    :param Boolean coverpage: Should a cover page be generated?
    """
    # use this to render the bulk of the document with the Cobalt XSLT renderer
    renderer = HTMLRenderer(act=document.doc)
    body_html = renderer.render_xml(document.document_xml)

    # find
    template_name = find_document_template(document)

    # and then render some boilerplate around it
    return render_to_string(template_name, {
        'document': document,
        'content_html': body_html,
        'renderer': renderer,
        'coverpage': coverpage,
    })


def find_document_template(document):
    """ Return the filename of a template to use to render this document.

    This takes into account the country, type, subtype and language of the document,
    providing a number of opportunities to adjust the rendering logic.
    """
    uri = document.doc.frbr_uri
    doctype = uri.doctype

    options = []
    if uri.subtype:
        options.append('_'.join([doctype, uri.subtype, document.language, uri.country]))
        options.append('_'.join([doctype, uri.subtype, document.language]))
        options.append('_'.join([doctype, uri.subtype, uri.country]))
        options.append('_'.join([doctype, uri.country]))
        options.append('_'.join([doctype, uri.subtype]))

    options.append('_'.join([doctype, document.language, uri.country]))
    options.append('_'.join([doctype, document.language]))
    options.append('_'.join([doctype, uri.country]))
    options.append(doctype)

    options = [f + '.html' for f in options]

    for option in options:
        try:
            if find_template(option):
                return option
        except TemplateDoesNotExist:
            pass

    raise ValueError("Couldn't find a template to use for %s. Tried: %s" % (uri, ', '.join(options)))


class DocumentViewMixin(object):
    queryset = Document.objects.filter(deleted__exact=False).prefetch_related('tags').all()

    def table_of_contents(self, document):
        # this updates the TOC entries by adding a 'url' component
        # based on the document's URI and the path of the TOC subcomponent
        uri = document.doc.frbr_uri
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
    permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)

    def perform_destroy(self, instance):
        if not instance.draft:
            raise MethodNotAllowed('DELETE', 'DELETE not allowed for published documents, mark as draft first.')
        instance.deleted = True
        instance.save()

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
                instance.save()
            except LxmlError as e:
                raise ValidationError({'content': ["Invalid XML: %s" % e.message]})

            return Response({'content': instance.document_xml})

    @detail_route(methods=['GET'])
    def toc(self, request, *args, **kwargs):
        """ This exposes a GET resource at ``/api/documents/1/toc`` which gives
        a table of contents for the document.
        """
        return Response({'toc': self.table_of_contents(self.get_object())})


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer

    @detail_route(methods=['GET'])
    def download(self, request, *args, **kwargs):
        attachment = self.get_object()
        return download_attachment(attachment)

    @detail_route(methods=['GET'])
    def view(self, request, *args, **kwargs):
        attachment = self.get_object()
        return view_attachment(attachment)

    def initial(self, request, **kwargs):
        self.document = self.lookup_document()
        super(AttachmentViewSet, self).initial(request, **kwargs)

    def lookup_document(self):
        qs = Document.objects.defer('document_xml')
        doc_id = self.kwargs['document_id']
        return get_object_or_404(qs, deleted__exact=False, id=doc_id)

    def get_queryset(self):
        return Attachment.objects.filter(document=self.document).all()

    def get_serializer_context(self):
        context = super(AttachmentViewSet, self).get_serializer_context()
        context['document'] = self.document
        return context


class PublishedDocumentDetailView(DocumentViewMixin,
                                  mixins.RetrieveModelMixin,
                                  mixins.ListModelMixin,
                                  viewsets.GenericViewSet):
    """
    The public read-only API for viewing and listing documents by FRBR URI.
    """
    queryset = DocumentViewMixin.queryset.filter(draft=False)

    serializer_class = DocumentSerializer
    # these determine what content negotiation takes place
    renderer_classes = (renderers.JSONRenderer, AkomaNtosoRenderer, renderers.StaticHTMLRenderer)

    def initial(self, request, **kwargs):
        super(PublishedDocumentDetailView, self).initial(request, **kwargs)
        # ensure the URI starts with a slash
        self.kwargs['frbr_uri'] = '/' + self.kwargs['frbr_uri']

    def get(self, request, **kwargs):
        # try parse it as an FRBR URI, if that succeeds, we'll lookup the document
        # that document matches, otherwise we'll assume they're trying to
        # list documents with a prefix URI match.
        try:
            self.frbr_uri = FrbrUri.parse(self.kwargs['frbr_uri'])

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

    def list(self, request):
        # force JSON for list view
        self.request.accepted_renderer = renderers.JSONRenderer()
        self.request.accepted_media_type = self.request.accepted_renderer.media_type
        return super(PublishedDocumentDetailView, self).list(request)

    def retrieve(self, request, *args, **kwargs):
        component = self.frbr_uri.expression_component or 'main'
        subcomponent = self.frbr_uri.expression_subcomponent
        format = self.request.accepted_renderer.format

        # get the document
        document = self.get_object()

        if subcomponent:
            element = document.doc.get_subcomponent(component, subcomponent)

        else:
            # special cases of the entire document

            # table of contents
            if (component, format) == ('toc', 'json'):
                serializer = self.get_serializer(document)
                return Response({'toc': self.table_of_contents(document)})

            # json description
            if (component, format) == ('main', 'json'):
                serializer = self.get_serializer(document)
                return Response(serializer.data)

            # entire thing
            if (component, format) == ('main', 'xml'):
                return Response(document.document_xml)

            # the item we're interested in
            element = document.doc.components().get(component)

        if element:
            if format == 'html':
                if component == 'main' and not subcomponent:
                    coverpage = self.request.GET.get('coverpage', 1) == '1'
                    return Response(document_to_html(document, coverpage=coverpage))
                else:
                    return Response(HTMLRenderer(act=document.doc).render(element))

            if format == 'xml':
                return Response(ET.tostring(element, pretty_print=True))

        raise Http404

    def get_object(self):
        """ Find and return one document, used by retrieve() """
        query = self.get_queryset().filter(frbr_uri=self.frbr_uri.work_uri())\

        # filter on expression date
        expr_date = self.frbr_uri.expression_date
        if expr_date:
            try:
                if expr_date == '@':
                    # earliest document
                    query = query.order_by('expression_date')

                elif expr_date[0] == '@':
                    # document at this date
                    query = query.filter(expression_date=arrow.get(expr_date[1:]).date())

                elif expr_date[0] == ':':
                    # latest document at or before this date
                    query = query\
                        .filter(expression_date__lte=arrow.get(expr_date[1:]).date())\
                        .order_by('-expression_date')

                else:
                    raise Http404("The expression date %s is not valid" % expr_date)

            except arrow.parser.ParserError:
                raise Http404("The expression date %s is not valid" % expr_date)

        else:
            # always get the latest expression
            query = query.order_by('-expression_date')

        obj = query.first()
        if obj is None:
            raise Http404("Document doesn't exist")

        if obj.language != self.frbr_uri.language:
            raise Http404("The document %s exists but is not available in the language '%s'"
                          % (self.frbr_uri.work_uri(), self.frbr_uri.language))

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj

    def filter_queryset(self, queryset):
        """ Filter the queryset, used by list() """
        queryset = queryset.filter(frbr_uri__istartswith=self.kwargs['frbr_uri'])
        if queryset.count() == 0:
            raise Http404
        return queryset

    def get_format_suffix(self, **kwargs):
        # we could also pull this from the parsed URI
        match = FORMAT_RE.search(self.kwargs['frbr_uri'])
        if match:
            # strip it from the uri
            self.kwargs['frbr_uri'] = self.kwargs['frbr_uri'][0:match.start()]
            return match.group(1)


class ConvertView(APIView):
    """
    Support for converting between two document types. This allows conversion from
    plain text, JSON, XML, and PDF to plain text, JSON, XML and HTML.
    """

    # Allow anyone to use this API, it uses POST but doesn't change
    # any documents in the database and so is safe.
    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        serializer, document = self.handle_input()
        output_format = serializer.validated_data.get('outputformat')
        return self.handle_output(document, output_format)

    def handle_input(self):
        self.fragment = self.request.data.get('fragment')
        document = None
        serializer = ConvertSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        input_format = serializer.validated_data.get('inputformat')

        upload = self.request.data.get('file')
        if upload:
            # we got a file
            try:
                document = self.get_importer().import_from_upload(upload)
                return serializer, document
            except ValueError as e:
                log.error("Error during import: %s" % e.message, exc_info=e)
                raise ValidationError({'file': e.message or "error during import"})

        elif input_format == 'application/json':
            doc_serializer = DocumentSerializer(
                data=self.request.data['content'],
                context={'request': self.request})
            doc_serializer.is_valid(raise_exception=True)
            document = doc_serializer.update_document(Document())

        elif input_format == 'text/plain':
            try:
                document = self.get_importer().import_from_text(self.request.data['content'])
            except ValueError as e:
                log.error("Error during import: %s" % e.message, exc_info=e)
                raise ValidationError({'content': e.message or "error during import"})

        if not document:
            raise ValidationError("Nothing to convert! Either 'file' or 'content' must be provided.")

        return serializer, document

    def handle_output(self, document, output_format):
        if output_format == 'application/json':
            if self.fragment:
                raise ValidationError("Cannot output application/json from a fragment")

            # disable tags, they can't be used without committing this object to the db
            document.tags = None

            doc_serializer = DocumentSerializer(instance=document, context={'request': self.request})
            data = doc_serializer.data
            data['content'] = document.document_xml
            return Response(data)

        if output_format == 'application/xml':
            if self.fragment:
                return Response({'output': document.to_xml()})
            else:
                return Response({'output': document.document_xml})

        if output_format == 'text/html':
            if self.fragment:
                return Response(HTMLRenderer().render(document.to_xml()))
            else:
                return Response({'output': document_to_html(document)})

        # TODO: handle plain text output

    def get_importer(self):
        importer = Importer()
        importer.fragment = self.request.data.get('fragment')
        importer.fragment_id_prefix = self.request.data.get('id_prefix')

        return importer


class LinkTermsView(APIView):
    """
    Support for running term discovery and linking on a document.
    """

    # Allow anyone to use this API, it uses POST but doesn't change
    # any documents in the database and so is safe.
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = LinkTermsSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        doc_serializer = DocumentSerializer(
            data=self.request.data['document'],
            context={'request': self.request})
        doc_serializer.is_valid(raise_exception=True)
        if not doc_serializer.validated_data.get('content'):
            raise ValidationError({'document': ["Content cannot be empty."]})

        document = doc_serializer.update_document(Document())
        self.link_terms(document)

        return Response({'document': {'content': document.document_xml}})

    def link_terms(self, doc):
        Slaw().link_terms(doc)
