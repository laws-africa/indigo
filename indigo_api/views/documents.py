import logging
import copy

from actstream import action
from django.shortcuts import redirect
from django.views import View
from django.views.decorators.cache import cache_control
from django.db.models import F
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import SearchQuery
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django_comments.models import Comment

from rest_framework.exceptions import ValidationError, MethodNotAllowed
from rest_framework.views import APIView
from rest_framework import mixins, viewsets, renderers, status
from rest_framework.generics import get_object_or_404, ListAPIView
from rest_framework.response import Response
from rest_framework.decorators import action as detail_route_action
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly, IsAuthenticated
from reversion import revisions as reversion
from django_filters.rest_framework import DjangoFilterBackend
from cobalt import FrbrUri, StructuredDocument, AkomaNtosoDocument

import lxml.html.diff
from lxml.etree import LxmlError

from indigo.analysis.differ import AttributeDiffer
from indigo.plugins import plugins
from ..models import Document, Annotation, DocumentActivity, Task
from ..serializers import DocumentSerializer, RenderSerializer, ParseSerializer, DocumentAPISerializer, VersionSerializer, AnnotationSerializer, DocumentActivitySerializer, TaskSerializer, DocumentDiffSerializer
from ..renderers import AkomaNtosoRenderer, PDFRenderer, EPUBRenderer, HTMLRenderer, ZIPRenderer
from indigo_api.exporters import HTMLExporter
from ..authz import DocumentPermissions, AnnotationPermissions, DocumentActivityPermission
from ..utils import Headline, SearchPagination, SearchRankCD, filename_candidates, find_best_static
from .misc import DEFAULT_PERMS

log = logging.getLogger(__name__)


# Default document fields that can be use to filter list views
DOCUMENT_FILTER_FIELDS = {
    'frbr_uri': ['exact', 'startswith'],
    'language': ['exact'],
    'draft': ['exact'],
    'expression_date': ['exact', 'lte', 'gte'],
}


class DocumentViewMixin(object):
    queryset = Document.objects\
        .undeleted()\
        .no_xml()\
        .prefetch_related('tags', 'created_by_user', 'updated_by_user',
                          'language', 'language__language',
                          'work', 'work__country',
                          'work__parent_work', 'work__repealed_by',
                          'work__amendments', 'work__amendments__amending_work', 'work__amendments__amended_work',
                          'work__taxonomies', 'work__taxonomies__vocabulary')

    def initial(self, request, **kwargs):
        super(DocumentViewMixin, self).initial(request, **kwargs)

        # some of our renderers want to bypass the serializer, so that we get access to the
        # raw data objects
        if getattr(self.request.accepted_renderer, 'serializer_class', None):
            self.serializer_class = self.request.accepted_renderer.serializer_class

    def table_of_contents(self, document, uri=None):
        return [t.as_dict() for t in document.table_of_contents()]


# Read/write REST API
class DocumentViewSet(DocumentViewMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """
    API endpoint that allows get, list, update and destroy, but not creation of documents.
    """
    serializer_class = DocumentSerializer
    permission_classes = DEFAULT_PERMS + (DjangoModelPermissionsOrAnonReadOnly, DocumentPermissions)
    renderer_classes = (renderers.JSONRenderer, PDFRenderer, EPUBRenderer,
                        HTMLRenderer, AkomaNtosoRenderer, ZIPRenderer,
                        renderers.BrowsableAPIRenderer)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = DOCUMENT_FILTER_FIELDS

    def perform_destroy(self, instance):
        if not instance.draft:
            raise MethodNotAllowed('DELETE', 'DELETE not allowed for published documents, mark as draft first.')
        instance.deleted = True
        action.send(self.request.user, verb='deleted', action_object=instance,
                    place_code=instance.work.place.place_code)
        instance.save()

    def perform_update(self, serializer):
        # check permissions just before saving, to prevent users
        # without publish permissions from setting draft = False
        if not DocumentPermissions().update_allowed(self.request, serializer):
            self.permission_denied(self.request)

        super(DocumentViewSet, self).perform_update(serializer)

    @detail_route_action(detail=True, methods=['GET', 'PUT'])
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
                raise ValidationError({'content': ["Invalid XML: %s" % str(e)]})

            return Response({'content': instance.document_xml})

    @detail_route_action(detail=True, methods=['GET'])
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


class AnnotationViewSet(DocumentResourceView, viewsets.ModelViewSet):
    queryset = Annotation.objects
    serializer_class = AnnotationSerializer
    permission_classes = DEFAULT_PERMS + (DjangoModelPermissionsOrAnonReadOnly, AnnotationPermissions)

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset).filter(document=self.document)
    
    def list(self, request, **kwargs):
        queryset = list(self.filter_queryset(self.get_queryset()))
        task_content_type = ContentType.objects.get_for_model(Task)

        fake_annotations = []
        for annotation in queryset:
            if annotation.task and annotation.in_reply_to is None:
                # the task linked to the annotation
                task = annotation.task
                # get the tasks comments
                task_comments = Comment.objects\
                        .filter(content_type=task_content_type, object_pk=task.id)

                for comment in task_comments:
                    fake_annotation = Annotation(
                        document=self.document,
                        text=comment.comment,
                        created_by_user=comment.user,
                        in_reply_to=annotation,
                        created_at=comment.submit_date,
                        updated_at=comment.submit_date,
                        anchor_id=annotation.anchor_id,
                    )

                    fake_annotations.append(fake_annotation)

        queryset += fake_annotations
        context = {}
        context['request'] = request
        results = AnnotationSerializer(queryset, many=True, context=context)
        data = {
            "count": len(queryset),
            "results": results.data,
        }
        return Response(data)

    @detail_route_action(detail=True, methods=['GET', 'POST'])
    def task(self, request, *args, **kwargs):
        """ Get or create a task for this annotation.
        """
        annotation = self.get_object()
        status = None

        if request.method == 'POST':
            if annotation.in_reply_to:
                raise MethodNotAllowed('POST', 'Cannot create a task for a reply annotation.')
            annotation.create_task(user=request.user)
            status = 201

        elif not annotation.task:
            raise Http404()

        data = TaskSerializer(instance=annotation.task, context={'request': request}).data
        return Response(data, status=status)


class RevisionViewSet(DocumentResourceView, viewsets.ReadOnlyModelViewSet):
    serializer_class = VersionSerializer
    # The permissions applied in this case are for reversion.Version
    permission_classes = DEFAULT_PERMS + (DjangoModelPermissionsOrAnonReadOnly,)

    @detail_route_action(detail=True, methods=['POST'])
    def restore(self, request, *args, **kwargs):
        # check permissions on the OLD object
        if not DocumentPermissions().has_object_permission(request, self, self.document):
            self.permission_denied(self.request)

        version = self.get_object()

        # check permissions on the NEW object
        document = version._object_version.object
        if not DocumentPermissions().has_object_permission(request, self, document):
            self.permission_denied(self.request)

        with reversion.create_revision():
            reversion.set_user(request.user)
            reversion.set_comment("Restored revision %s" % version.id)
            version.revision.revert()

        return Response(status=200)

    @detail_route_action(detail=True, methods=['GET'])
    @cache_control(public=True, max_age=24 * 3600)
    def diff(self, request, *args, **kwargs):
        # this can be cached because the underlying data won't change (although
        # the formatting might)
        version = self.get_object()

        # most recent version just before this one
        old_version = self.get_queryset().filter(id__lt=version.id).first()

        differ = AttributeDiffer()

        if old_version:
            old_document = old_version._object_version.object
            old_document.document_xml = differ.preprocess_document_diff(old_document.document_xml)
            old_html = old_document.to_html()
        else:
            old_html = ""

        new_document = version._object_version.object
        new_document.document_xml = differ.preprocess_document_diff(new_document.document_xml)
        new_html = new_document.to_html()

        old_tree = lxml.html.fromstring(old_html) if old_html else None
        new_tree = lxml.html.fromstring(new_html)
        n_changes = differ.diff_document_html(old_tree, new_tree)

        diff = lxml.html.tostring(new_tree, encoding='unicode')

        # TODO: include other diff'd attributes

        return Response({
            'content': diff,
            'n_changes': n_changes,
        })

    def get_queryset(self):
        return self.document.versions().defer('serialized_data')


class DocumentActivityViewSet(DocumentResourceView,
                              mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              viewsets.GenericViewSet):
    """ API endpoint to see who's working in a document.

    Because this "locks" a document, only users who have permission to edit the document
    can create an activity object.
    """
    serializer_class = DocumentActivitySerializer
    permission_classes = DEFAULT_PERMS + (DjangoModelPermissionsOrAnonReadOnly, DocumentActivityPermission)

    def get_queryset(self):
        return self.document.activities.prefetch_related('user').all()

    def list(self, request, *args, **kwargs):
        # clean up old activity
        DocumentActivity.vacuum(self.document)
        return super(DocumentActivityViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # if they've provided additional finished nonces, clear those out
        if request.data.get('finished_nonces'):
            nonces = request.data['finished_nonces'].split(',')
            self.get_queryset().filter(user=request.user, nonce__in=nonces).delete()

        # either create a new activity object, or update it
        self.get_queryset().update_or_create(
            document=self.document, user=request.user, nonce=request.data['nonce'],
            defaults={'updated_at': timezone.now()},
        )
        return self.list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        activity = self.get_queryset().filter(user=request.user, nonce=request.data['nonce']).first()
        if activity:
            activity.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ParseView(DocumentResourceView, APIView):
    """ Parse text into Akoma Ntoso, returning Akoma Ntoso XML.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, document_id):
        serializer = ParseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fragment = serializer.validated_data.get('fragment')
        frbr_uri = self.document.work_uri

        importer = plugins.for_locale('importer', frbr_uri.country, frbr_uri.language, frbr_uri.locality)
        importer.fragment = fragment
        importer.fragment_id_prefix = serializer.validated_data.get('id_prefix')

        try:
            text = serializer.validated_data.get('content')
            xml = importer.import_from_text(text, frbr_uri.work_uri(), '.txt')
        except ValueError as e:
            log.error("Error during import: %s" % str(e), exc_info=e)
            raise ValidationError({'content': str(e) or "error during import"})

        if fragment:
            # clean up encodings
            doc = AkomaNtosoDocument(xml)
            xml = doc.to_xml(encoding='unicode')
        else:
            # The importer doesn't have enough information to give us a complete document
            # including the meta section, so it's empty or incorrect. We fold in the meta section
            # from the existing document, so that we return a complete document to the caller.
            klass = StructuredDocument.for_document_type(frbr_uri.doctype)
            doc = klass(xml)
            doc.main.replace(doc.meta, copy.deepcopy(self.document.doc.meta))
            xml = doc.to_xml(encoding='unicode')

        return Response({'output': xml})


class RenderView(DocumentResourceView, APIView):
    """ Support for rendering a document on the server.
    """
    permission_classes = ()
    coverpage_only = True

    def post(self, request, document_id):
        serializer = RenderSerializer(instance=self.document, data=request.data)
        serializer.is_valid(raise_exception=True)
        document = DocumentSerializer().update_document(self.document, validated_data=serializer.validated_data['document'])

        if self.coverpage_only:
            renderer = HTMLExporter()
            renderer.media_url = reverse('document-detail', kwargs={'pk': document.id}) + '/'
            html = renderer.render_coverpage(document)
            return Response({'output': html})
        else:
            return Response({'output': document.to_html()})


class LinkTermsView(DocumentResourceView, APIView):
    """ Support for running term discovery and linking on a document.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, document_id):
        serializer = DocumentAPISerializer(instance=self.document, data=self.request.data)
        serializer.fields['document'].fields['content'].required = True
        serializer.is_valid(raise_exception=True)
        document = serializer.fields['document'].update_document(self.document, serializer.validated_data['document'])

        self.link_terms(document)

        return Response({'document': {'content': document.document_xml}})

    def link_terms(self, doc):
        finder = plugins.for_document('terms', doc)
        if finder:
            finder.find_terms_in_document(doc)


class LinkReferencesView(DocumentResourceView, APIView):
    """ Find and link internal references and references to other works.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, document_id):
        serializer = DocumentAPISerializer(instance=self.document, data=self.request.data)
        serializer.fields['document'].fields['content'].required = True
        serializer.is_valid(raise_exception=True)
        document = serializer.fields['document'].update_document(self.document, serializer.validated_data['document'])

        self.find_references(document)

        return Response({'document': {'content': document.document_xml}})

    def find_references(self, document):
        finder = plugins.for_document('refs', document)
        if finder:
            finder.find_references_in_document(document)

        finder = plugins.for_document('refs-subtypes', document)
        if finder:
            finder.find_references_in_document(document)

        finder = plugins.for_document('refs-cap', document)
        if finder:
            finder.find_references_in_document(document)

        finder = plugins.for_document('refs-act-names', document)
        if finder:
            finder.find_references_in_document(document)

        finder = plugins.for_document('internal-refs', document)
        if finder:
            finder.find_references_in_document(document)


class MarkUpItalicsTermsView(DocumentResourceView, APIView):
    """ Find and mark up italics terms.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, document_id):
        serializer = DocumentAPISerializer(instance=self.document, data=self.request.data)
        serializer.fields['document'].fields['content'].required = True
        serializer.is_valid(raise_exception=True)
        document = serializer.fields['document'].update_document(self.document, serializer.validated_data['document'])

        self.mark_up_italics(document)

        return Response({'document': {'content': document.document_xml}})

    def mark_up_italics(self, document):
        italics_terms_finder = plugins.for_document('italics-terms', document)
        italics_terms = document.work.country.italics_terms
        if italics_terms_finder and italics_terms:
            italics_terms_finder.mark_up_italics_in_document(document, italics_terms)


class SearchView(DocumentViewMixin, ListAPIView):
    """ Search and return either works, or documents, depending on `scope`.

    This view drives in-app search and returns works.
    """
    serializer_class = DocumentSerializer
    pagination_class = SearchPagination
    filter_backends = (DjangoFilterBackend,)
    filter_fields = DOCUMENT_FILTER_FIELDS
    permission_classes = DEFAULT_PERMS + (DjangoModelPermissionsOrAnonReadOnly,)

    # Search scope, either 'documents' or 'works'.
    scope = 'works'

    def filter_queryset(self, queryset):
        query = SearchQuery(self.request.query_params.get('q'))

        queryset = super(SearchView, self).filter_queryset(queryset)
        queryset = queryset.filter(search_vector=query)

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
            serializer.data[i]['_rank'] = doc.rank
            serializer.data[i]['_snippet'] = doc.snippet

        return serializer


class DocumentDiffView(DocumentResourceView, APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, document_id):
        serializer = DocumentDiffSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        differ = AttributeDiffer()

        local_doc = self.document

        # set this up to be the modified document
        remote_doc = Document.objects.get(pk=local_doc.pk)
        serializer.fields['document'].update_document(local_doc, serializer.validated_data['document'])

        local_doc.content = differ.preprocess_document_diff(local_doc.document_xml).decode('utf-8')
        remote_doc.content = differ.preprocess_document_diff(remote_doc.document_xml).decode('utf-8')

        element_id = serializer.validated_data.get('element_id')
        if element_id:
            # handle certain elements that don't have ids
            if element_id in ['preface', 'preamble', 'components']:
                xpath = f'//a:{element_id}'
            else:
                xpath = f'//a:*[@id="{element_id}"]'

            # diff just this element
            local_element = local_doc.doc.root.xpath(xpath, namespaces={'a': local_doc.doc.namespace})
            remote_element = remote_doc.doc.root.xpath(xpath, namespaces={'a': local_doc.doc.namespace})

            local_html = local_doc.to_html(element=local_element[0]) if len(local_element) else None
            remote_html = remote_doc.to_html(element=remote_element[0]) if len(remote_element) else None
        else:
            # diff the whole document
            local_html = local_doc.to_html()
            remote_html = remote_doc.to_html()

        local_tree = lxml.html.fromstring(local_html or "<div></div>")
        remote_tree = lxml.html.fromstring(remote_html) if remote_html else None
        n_changes = differ.diff_document_html(remote_tree, local_tree)

        diff = lxml.html.tostring(local_tree, encoding='utf-8')

        # TODO: include other diff'd attributes

        return Response({
            'html_diff': diff,
            'n_changes': n_changes,
        })


class StaticFinderView(DocumentResourceView, View):
    """ This view looks for a static file (such as text.xsl, or html.xsl) suitable for use with this document,
    based on its FRBR URI. Because there are a number of options to try, it's faster to do it on the server than
    the client, and then redirect the caller to the appropriate static file URL.

    eg. a request for text.xsl might find text_act-eng-za.xsl
    """
    def get(self, request, document_id, filename):
        if '.' in filename:
            prefix, suffix = filename.split('.', 1)
            suffix = '.' + suffix
        else:
            prefix, suffix = filename, ''

        candidates = filename_candidates(self.lookup_document(), f'{prefix}_', suffix)
        best = find_best_static(candidates, actual=False)
        if best:
            return redirect(static(best))

        raise Http404()
