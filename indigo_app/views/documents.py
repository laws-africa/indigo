import json

from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import DetailView
from lxml import etree

import bluebell
import cobalt
from cobalt import Portion
from indigo.plugins import plugins
from indigo_api.models import Document, Country, Subtype, Work
from indigo_api.serializers import DocumentSerializer, WorkSerializer, WorkAmendmentSerializer
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
        context['work_json'] = json.dumps(WorkSerializer(instance=doc.work, context={'request': self.request}).data)
        context['document_json'] = json.dumps(DocumentSerializer(instance=doc, context={'request': self.request}).data)
        # expressions
        context['expressions_json'] = json.dumps(
            DocumentSerializer(context={'request': self.request}, many=True)
            .to_representation(
                doc.work.expressions().all()
            ))
        context['comparison_expressions'] = doc.work.expressions().filter(language=doc.language).order_by('-expression_date')
        context['place'] = doc.work.place
        context['country'] = doc.work.country
        context['locality'] = doc.work.locality

        # TODO do this in a better place
        context['countries'] = Country.objects.select_related('country').prefetch_related('localities', 'publication_set', 'country').all()

        context['document_content_json'] = self.get_document_content_json(doc)

        # add 'numbered_title_localised' to each amendment
        amendments = WorkAmendmentSerializer(context={'request': self.request}, many=True)\
            .to_representation(doc.work.amendments)
        plugin = plugins.for_document('work-detail', doc)
        if plugin:
            for a in amendments:
                amending_work = Work.objects.get(frbr_uri=a['amending_work']['frbr_uri'])
                a['amending_work']['numbered_title_localised'] = plugin.work_numbered_title(amending_work)
        context['amendments_json'] = json.dumps(amendments)

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

        return context

    def get_document_content_json(self, document):
        return json.dumps(document.document_xml)


class ChooseDocumentProvisionView(AbstractAuthedIndigoView, DetailView):
    model = Document
    context_object_name = 'document'
    pk_url_kwarg = 'doc_id'
    template_name = 'indigo_api/document/_provisions.html'

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

    def has_permission(self):
        return self.request.user.is_superuser


class DocumentProvisionDetailView(DocumentDetailView):
    eid = None
    provision_xml = None

    def get(self, request, *args, **kwargs):
        document = self.get_object()
        self.eid = self.kwargs.get('eid')
        provision_xml = document.doc.get_portion_element(self.eid)
        if not provision_xml:
            messages.error(request, _("No provision with this id found: '%(eid)s'") % {"eid": self.eid})
            return redirect('choose_document_provision', doc_id=document.id)
        portion = Portion()
        portion.frbr_uri = document.frbr_uri
        portion.main_content.append(provision_xml)
        self.provision_xml = portion.main
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['provision_eid'] = self.eid
        return context

    def get_document_content_json(self, document):
        return json.dumps(etree.tostring(self.provision_xml, encoding='unicode'))

    def has_permission(self):
        return self.request.user.is_superuser


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
