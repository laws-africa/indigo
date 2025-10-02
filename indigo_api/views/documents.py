import copy
import datetime
import json
import logging

from actstream import action
from asgiref.sync import sync_to_async
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import DetailView
from django_comments.models import Comment
from django_filters.rest_framework import DjangoFilterBackend
from lxml import etree
from rest_framework import mixins, viewsets, renderers, status
from rest_framework.decorators import action as detail_route_action
from rest_framework.exceptions import ValidationError, MethodNotAllowed
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from reversion import revisions as reversion

from cobalt import StructuredDocument
from indigo.analysis.differ import AKNHTMLDiffer
from indigo.analysis.refs.base import markup_document_refs
from indigo.plugins import plugins
from indigo_api.data_migrations import DefinitionsIntoBlockContainers
from indigo_api.exporters import HTMLExporter
from indigo_app.views.base import AsyncDispatchMixin, AbstractAuthedIndigoView
from .misc import DEFAULT_PERMS
from ..authz import DocumentPermissions, AnnotationPermissions, ModelPermissions, RelatedDocumentPermissions, \
    RevisionPermissions
from ..models import Document, Annotation, DocumentActivity, Task
from ..renderers import AkomaNtosoRenderer, PDFRenderer, EPUBRenderer, HTMLRenderer, ZIPRenderer
from ..serializers import DocumentSerializer, RenderSerializer, ParseSerializer, DocumentAPISerializer, \
    VersionSerializer, AnnotationSerializer, DocumentActivitySerializer, TaskSerializer
from ..utils import filename_candidates, find_best_static, adiff_html_str

log = logging.getLogger(__name__)


# Default document fields that can be use to filter list views
DOCUMENT_FILTER_FIELDS = {
    'frbr_uri': ['exact', 'startswith'],
    'language': ['exact'],
    'draft': ['exact'],
    'expression_date': ['exact', 'lte', 'gte'],
}


class DocumentViewMixin:
    queryset = Document.objects\
        .undeleted()\
        .no_xml()\
        .prefetch_related('created_by_user', 'updated_by_user',
                          'language', 'language__language',
                          'work', 'work__country',
                          'work__parent_work', 'work__repealed_by',
                          'work__amendments', 'work__amendments__amending_work', 'work__amendments__amended_work')

    def initial(self, request, **kwargs):
        super().initial(request, **kwargs)

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
    permission_classes = DEFAULT_PERMS + (ModelPermissions, DocumentPermissions)
    renderer_classes = (renderers.JSONRenderer, PDFRenderer, EPUBRenderer,
                        HTMLRenderer, AkomaNtosoRenderer, ZIPRenderer,
                        renderers.BrowsableAPIRenderer)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = DOCUMENT_FILTER_FIELDS

    def perform_destroy(self, instance):
        if not instance.draft:
            raise MethodNotAllowed('DELETE', _('DELETE not allowed for published documents, mark as a draft first.'))
        instance.deleted = True
        action.send(self.request.user, verb='deleted', action_object=instance,
                    place_code=instance.work.place.place_code)
        instance.save()

    def perform_update(self, serializer):
        # check permissions just before saving, to prevent users
        # without publish permissions from setting draft = False
        if not DocumentPermissions().update_allowed(self.request, serializer):
            self.permission_denied(self.request)

        super().perform_update(serializer)

    @detail_route_action(detail=True, methods=['GET'])
    def content(self, request, *args, **kwargs):
        """ This exposes a GET resource at ``/api/documents/1/content`` which allows
        the content of the document to be fetched independently of the metadata. This
        is useful because the content can be large.
        """
        if request.method == 'GET':
            return Response({'content': self.get_object().document_xml})

    @detail_route_action(detail=True, methods=['GET'])
    def toc(self, request, *args, **kwargs):
        """ This exposes a GET resource at ``/api/documents/1/toc`` which gives
        a table of contents for the document.
        """
        return Response({'toc': self.table_of_contents(self.get_object())})


class DocumentResourceView:
    """ Helper mixin for views that hang off of a document URL.

    Enforces permissions for the linked document.
    """
    permission_classes = DEFAULT_PERMS + (RelatedDocumentPermissions,)

    def initial(self, request, **kwargs):
        self.document = self.lookup_document()
        super().initial(request, **kwargs)

    def lookup_document(self):
        qs = Document.objects.undeleted().no_xml()
        doc_id = self.kwargs['document_id']
        return get_object_or_404(qs, id=doc_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['document'] = self.document
        return context


class AnnotationViewSet(DocumentResourceView, viewsets.ModelViewSet):
    queryset = Annotation.objects\
        .select_related('created_by_user', 'task', 'task__updated_by_user', 'task__created_by_user',
                        'task__assigned_to', 'task__country', 'task__locality', 'task__work')
    serializer_class = AnnotationSerializer
    permission_classes = DEFAULT_PERMS + (ModelPermissions, AnnotationPermissions)

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset).filter(document=self.document)
    
    def list(self, request, **kwargs):
        queryset = list(self.filter_queryset(self.get_queryset()))
        task_content_type = ContentType.objects.get_for_model(Task)

        # load task comments as fake annotations
        tasks = {a.task_id: a for a in queryset if a.task_id and a.in_reply_to is None}
        task_comments = Comment.objects.filter(content_type=task_content_type, object_pk__in=list(tasks.keys()))
        fake_annotations = [Annotation(
            document=self.document,
            text=comment.comment,
            created_by_user=comment.user,
            in_reply_to=tasks[int(comment.object_pk)],
            created_at=comment.submit_date,
            updated_at=comment.submit_date,
            anchor_id=tasks[int(comment.object_pk)].anchor_id,
        ) for comment in task_comments]

        queryset += fake_annotations
        context = {'request': request}
        results = self.serializer_class(queryset, many=True, context=context)
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
                raise MethodNotAllowed('POST', _('Cannot create a task for a reply annotation.'))
            annotation.create_task(user=request.user)
            status = 201

        elif not annotation.task:
            raise Http404()

        data = TaskSerializer(instance=annotation.task, context={'request': request}).data
        return Response(data, status=status)


class RevisionViewSet(DocumentResourceView, viewsets.ReadOnlyModelViewSet):
    serializer_class = VersionSerializer
    # The permissions applied in this case are for reversion.Version
    permission_classes = DEFAULT_PERMS + (ModelPermissions, RevisionPermissions)

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

    def get_queryset(self):
        return self.document.versions().defer('serialized_data')


class AsyncDocumentResourceViewMixin(AsyncDispatchMixin, DocumentResourceView):
    """Helper mixin to replicate some DRF functionality for use with async views."""
    def check_permissions(self, request):
        for perm in self.permission_classes:
            if not perm().has_permission(request, self):
                raise PermissionDenied()

    def check_object_permissions(self, request, object):
        for perm in self.permission_classes:
            if hasattr(perm, 'has_object_permission'):
                if not perm().has_object_permission(request, self, object):
                    raise PermissionDenied()


class RevisionDiffView(AsyncDocumentResourceViewMixin, AbstractAuthedIndigoView, DetailView):
    """Handles diffs between two revisions of a document.

    This could be implemented as a detail view of RevisionViewSet, but it runs asynchronously which DRF doesn't yet
    support. So we have to re-implement some basics like permissions checks.
    """
    permission_classes = RevisionViewSet.permission_classes

    def get_queryset(self):
        return self.document.versions().defer('serialized_data')

    @sync_to_async
    def prepare(self, request):
        self.document = self.lookup_document()
        self.check_permissions(request)

        # this can be cached because the underlying data won't change (although the formatting might)
        version = self.get_object()
        self.check_object_permissions(request, version)

        # most recent version just before this one
        old_version = self.get_queryset().filter(id__lt=version.id).first()

        differ = AKNHTMLDiffer()

        if old_version:
            old_document = old_version._object_version.object
            old_document.document_xml = differ.preprocess_xml_str(old_document.document_xml)
            old_html = old_document.to_html()
        else:
            old_html = ""

        new_document = version._object_version.object
        new_document.document_xml = differ.preprocess_xml_str(new_document.document_xml)
        new_html = new_document.to_html()

        return old_html, new_html

    async def get(self, request, *args, **kwargs):
        old_html, new_html = await self.prepare(request)
        diff = await adiff_html_str(old_html, new_html)
        # show whole document if it hasn't changed
        diff = diff or ("<div>" + new_html + "</div>")
        return JsonResponse({
            'content': diff,
        })


class DocumentActivityViewSet(DocumentResourceView,
                              mixins.ListModelMixin,
                              mixins.CreateModelMixin,
                              viewsets.GenericViewSet):
    """ API endpoint to see who's working in a document.

    Because this "locks" a document, only users who have permission to edit the document
    can create an activity object.
    """
    serializer_class = DocumentActivitySerializer
    permission_classes = DEFAULT_PERMS + (ModelPermissions, RelatedDocumentPermissions)

    def get_queryset(self):
        return self.document.activities.prefetch_related('user').all()

    def filter_queryset(self, queryset):
        # only return entries that aren't stale
        threshold = timezone.now() - datetime.timedelta(seconds=DocumentActivity.DEAD_SECS)
        return queryset.filter(updated_at__gt=threshold)

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
    def post(self, request, document_id):
        serializer = ParseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fragment = serializer.validated_data.get('fragment')
        frbr_uri = self.document.expression_uri

        importer = plugins.for_locale('importer', frbr_uri.country, frbr_uri.language, frbr_uri.locality)
        importer.fragment = fragment
        importer.fragment_id_prefix = serializer.validated_data.get('id_prefix')

        text = serializer.validated_data.get('content')
        try:
            xml = importer.parse_from_text(text, frbr_uri)
        except ValueError as e:
            log.warning(f"Error during import: {e}", exc_info=e)
            log.warning(f"Full text being parsed (delimited with ---XXX---):\n---XXX---\n{text}\n---XXX---")
            raise ValidationError({'content': str(e) or _("Error during import")})

        if not fragment:
            # The importer doesn't have enough information to give us a complete document
            # including the meta section, so it's empty or incorrect. We fold in the meta section
            # from the existing document, so that we return a complete document to the caller.
            klass = StructuredDocument.for_document_type(frbr_uri.doctype)
            doc = klass(xml)
            doc.main.replace(doc.meta, copy.deepcopy(self.document.doc.meta))
            doc.frbr_uri = frbr_uri
            xml = doc.to_xml(encoding='unicode')

        return Response({'output': xml})


class RenderView(DocumentResourceView, APIView):
    """ Support for rendering a document on the server.
    """
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


class ManipulateXmlView(DocumentResourceView, APIView):
    serializer = None
    use_full_xml = False

    def post(self, request, document_id):
        self.serializer = DocumentAPISerializer(instance=self.document, data=self.request.data)
        self.serializer.use_full_xml = self.use_full_xml
        self.serializer.is_valid(raise_exception=True)
        self.serializer.update_document()
        self.manipulate_xml()
        return Response({'xml': self.serializer.updated_xml()})

    def manipulate_xml(self):
        raise NotImplementedError()


class LinkTermsView(ManipulateXmlView):
    """ Support for running term discovery and linking on a document.
    """
    use_full_xml = True

    def manipulate_xml(self):
        finder = plugins.for_document('terms', self.document)
        if finder:
            if self.serializer.validated_data.get('provision_eid'):
                finder.link_terms_in_document(self.document)
            else:
                finder.find_terms_in_document(self.document)


class LinkReferencesView(ManipulateXmlView):
    """ Find and link internal references and references to other works.
    """
    use_full_xml = True

    def manipulate_xml(self):
        markup_document_refs(self.document)


class MarkUpItalicsTermsView(ManipulateXmlView):
    """ Find and mark up italics terms.
    """
    def manipulate_xml(self):
        italics_terms_finder = plugins.for_document('italics-terms', self.document)
        italics_terms = self.document.work.country.italics_terms
        if italics_terms_finder and italics_terms:
            italics_terms_finder.mark_up_italics_in_document(self.document, italics_terms)


class SentenceCaseHeadingsView(ManipulateXmlView):
    """ Sentence case headings. Also apply accents as needed / relevant.
    """
    def manipulate_xml(self):
        sentence_caser = plugins.for_document('sentence-caser', self.document)
        if sentence_caser:
            sentence_caser.sentence_case_headings_in_document(self.document)


class DefinitionsIntoBlockContainersView(ManipulateXmlView):
    """ Wrap definitions that aren't already in a blockContainer in one.
    """
    def manipulate_xml(self):
        definitions_updater = DefinitionsIntoBlockContainers()
        definitions_updater.migrate_document(self.document)


class DocumentDiffView(AsyncDocumentResourceViewMixin, AbstractAuthedIndigoView, View):
    @sync_to_async
    def prepare(self, request):
        """Do database-related preparation in a sync manner, including rendering."""
        self.document = local_doc = self.lookup_document()
        self.check_permissions(request)

        data = json.loads(self.request.body)
        serializer = DocumentAPISerializer(instance=local_doc, data=data)
        serializer.use_full_xml = False
        serializer.is_valid(raise_exception=True)

        # set this up to be the modified document
        remote_doc = Document.objects.get(pk=local_doc.pk)

        # this will set the local_doc's content as the <portion> in provision mode,
        # and update it with the latest unsaved changes regardless
        serializer.set_content()

        differ = AKNHTMLDiffer()
        local_doc.content = differ.preprocess_xml_str(local_doc.document_xml)

        provision_eid = serializer.validated_data.get('provision_eid')
        if provision_eid:
            portion = remote_doc.get_portion(provision_eid)
            if portion:
                # the same structure as the 'xml' we're getting from the browser: akn/portion/portionBody/element
                remote_xml = etree.tostring(portion.root, encoding='unicode')
                remote_doc.work.work_uri.doctype = 'portion'
                remote_doc.content = differ.preprocess_xml_str(remote_xml)

        else:
            # full document mode
            remote_doc.content = differ.preprocess_xml_str(remote_doc.document_xml)

        element_id = serializer.validated_data.get('element_id')
        if element_id:
            # handle certain elements that don't have ids
            if element_id in ['preface', 'preamble', 'components']:
                xpath = f'//a:{element_id}'
            else:
                xpath = f'//a:*[@eId="{element_id}"]'

            # diff just this element
            local_element = local_doc.doc.root.xpath(xpath, namespaces={'a': local_doc.doc.namespace})
            remote_element = remote_doc.doc.root.xpath(xpath, namespaces={'a': local_doc.doc.namespace})

            local_html = local_doc.to_html(element=local_element[0]) if len(local_element) else None
            remote_html = remote_doc.to_html(element=remote_element[0]) if len(remote_element) else None
        else:
            # diff the whole document
            local_html = local_doc.to_html()
            remote_html = remote_doc.to_html()

        return remote_html, local_html

    async def post(self, request, document_id):
        remote_html, local_html = await self.prepare(request)
        diff = await adiff_html_str(remote_html, local_html)
        # diff is None if there is no difference, in which case just return the remote HTML
        diff = diff or ("<div>" + (remote_html or '') + "</div>")

        return JsonResponse({
            'html_diff': diff
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
