import json
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import DetailView
from lxml import etree

import bluebell
import cobalt
from bluebell.xml import XmlGenerator
from indigo.plugins import plugins
from indigo.xmlutils import rewrite_all_attachment_work_components
from indigo_api.models import Document, Country, Subtype, Amendment, Task
from indigo_app.serializers import WorkAmendmentDetailSerializer, WorkDetailSerializer, DocumentDetailSerializer
from indigo_api.views.documents import DocumentViewSet
from indigo_app.forms import DocumentForm
from .base import AbstractAuthedIndigoView


class DocumentDetailView(AbstractAuthedIndigoView, DetailView):
    model = Document
    context_object_name = 'document'
    pk_url_kwarg = 'doc_id'
    template_name = 'indigo_api/document/show.html'
    permission_required = ('indigo_api.view_document',)

    def get_object(self, queryset=None):
        doc = super().get_object(queryset)
        if doc.deleted:
            raise Http404()
        return doc

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        doc = self.object

        context['work'] = doc.work
        context['work_json'] = json.dumps(WorkDetailSerializer(instance=doc.work, context={'request': self.request}).data)
        context['document_json'] = json.dumps(DocumentDetailSerializer(instance=doc, context={'request': self.request}).data)
        # expressions
        context['expressions_json'] = json.dumps(
            DocumentDetailSerializer(context={'request': self.request}, many=True)
            .to_representation(
                doc.work.expressions().all()
            ))
        context['comparison_expressions'] = list(doc.work.expressions().filter(language=doc.language).order_by('-expression_date'))
        # don't compare by default when editing the whole document
        context['default_comparison_id'] = None
        context['place'] = doc.work.place
        context['country'] = doc.work.country
        context['locality'] = doc.work.locality

        # TODO do this in a better place
        context['countries'] = Country.objects.select_related('country').prefetch_related('localities', 'publication_set', 'country').all()

        context['document_content_json'] = self.get_document_content_json(doc)

        # add 'numbered_title_localised' to each amendment
        plugin = plugins.for_document('work-detail', doc)
        context["amendments_json"] = json.dumps(
            WorkAmendmentDetailSerializer(
                context={'request': self.request, 'work_detail_plugin': plugin},
                many=True,
            ).to_representation(
                Amendment.objects.filter(amended_work=doc.work)
                .select_related('amending_work', 'amending_work__publication_document')
                .prefetch_related('amending_work__chapter_numbers')
            )
        )
        context['form'] = DocumentForm(instance=doc)
        context['subtypes'] = Subtype.objects.order_by('name').all()
        context['user_can_edit'] = (
            self.request.user.is_authenticated
            and self.request.user.has_perm('indigo_api.change_document')
            and self.request.user.editor.has_country_permission(doc.work.country))

        context['download_formats'] = [{
            'url': reverse('document-detail', kwargs={'pk': doc.id, 'format': r.format}) + getattr(r, 'suffix', ''),
            'icon': r.icon,
            'title': r.title
        } for r in DocumentViewSet.renderer_classes if hasattr(r, 'icon')]
        context['download_formats'].sort(key=lambda f: f['title'])

        if settings.INDIGO['USE_PYODIDE']:
            context['pyodide_packages_json'] = json.dumps([
                f'cobalt=={cobalt.__version__}',
                f'bluebell-akn=={bluebell.__version__}',
            ])

        context['related_tasks'] = list(self.get_related_tasks())

        return context

    def get_related_tasks(self):
        return Task.objects.filter(work=self.object.work).filter(
            Q(timeline_date=self.object.expression_date) | Q(document=self.object)
        ).order_by('pk')

    def get_document_content_json(self, document):
        return json.dumps(document.document_xml)


class ChooseDocumentProvisionView(AbstractAuthedIndigoView, DetailView):
    model = Document
    context_object_name = 'document'
    pk_url_kwarg = 'doc_id'
    template_name = 'indigo_api/document/_provisions.html'
    permission_required = ('indigo_api.publish_document',)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['toc_json'] = self.get_toc_json()
        context['country'] = self.object.work.country
        context['place'] = self.object.work.place
        context['work'] = self.object.work
        return context

    def get_toc_json(self):
        def descend_toc_dict(items):
            for item in items:
                yield item
                for descendant in descend_toc_dict(item['children']):
                    yield descendant

        toc = [t.as_dict() for t in self.object.table_of_contents()]
        for elem in descend_toc_dict(toc):
            elem['href'] = reverse('document_provision', kwargs={'doc_id': int(self.kwargs['doc_id']), 'eid': elem['id']})
        return json.dumps(toc)


class DocumentProvisionDetailView(DocumentDetailView):
    eid = None
    provision_xml = None
    permission_required = ('indigo_api.publish_document',)

    def get(self, request, *args, **kwargs):
        document = self.get_object()
        self.eid = self.kwargs.get('eid')
        provision_xml = document.get_portion(self.eid)
        if provision_xml is None:
            messages.error(request, _("No provision with this id found: '%(eid)s'") % {"eid": self.eid})
            return redirect('choose_document_provision', doc_id=document.id)
        self.provision_xml = provision_xml.main
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['provision_eid'] = self.eid
        context['provision_counters'], context['eid_counter'], context['attachment_counters'] = self.get_counters()
        # in provision editing mode, compare to the previous point in time by default if there is one
        previous_documents = context['comparison_expressions'].exclude(expression_date__gte=self.object.expression_date)
        context['default_comparison_id'] = previous_documents.first().pk if previous_documents else None
        return context

    def get_document_content_json(self, document):
        return json.dumps(etree.tostring(self.provision_xml, encoding='unicode'))

    def get_counters(self):
        """ Generate provision and eid counters based on the content preceding our element.
            This way we don't end up 'correcting' e.g. part_II_2 to part_II,
             because the context will now be aware of the preceding part_II that isn't being edited.
        """
        root = etree.fromstring(self.object.document_xml)
        element = root.xpath(f'.//a:*[@eId="{self.eid}"]', namespaces={'a': self.object.doc.namespace})[0]
        parent = element.getparent()
        # remove everything from our element onwards (inclusive) from the tree
        for sibling in element.itersiblings():
            # this will remove e.g. parts III, IV, etc -- or if we're lower down, e.g. part_II__sec_3__subsec_2 etc
            parent.remove(sibling)
        parent.remove(element)
        # now remove all the ancestors' following siblings too, e.g. attachments,
        # or e.g. part_II__sec_4, part_III, up to attachments
        while parent is not None:
            for aunt in parent.itersiblings():
                aunt.getparent().remove(aunt)
            parent = parent.getparent()

        generator = XmlGenerator(self.object.frbr_uri)
        generator.generate_eids(root)
        doc = cobalt.StructuredDocument.for_document_type(self.object.work.work_uri.doctype)(etree.tostring(root, encoding='unicode'))
        attachment_counters = {'__attachments': rewrite_all_attachment_work_components(doc)}
        return json.dumps(generator.ids.counters), json.dumps(generator.ids.eid_counter), json.dumps(attachment_counters)


class DocumentPopupView(AbstractAuthedIndigoView, DetailView):
    model = Document
    context_object_name = 'document'
    pk_url_kwarg = 'doc_id'
    template_name = 'indigo_api/document_popup.html'
    queryset = Document.objects.no_xml().undeleted()
    permission_required = ('indigo_api.view_document',)

    def get_object(self, queryset=None):
        doc = super(DocumentPopupView, self).get_object(queryset)
        if doc.deleted:
            raise Http404()
        return doc
