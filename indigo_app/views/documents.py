import json

from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView
from lxml import etree

from indigo.plugins import plugins
from indigo_api.models import Document, Country, Subtype, Work
from indigo_api.serializers import DocumentSerializer, WorkSerializer, WorkAmendmentSerializer
from indigo_api.views.documents import DocumentViewSet
from indigo_app.forms import DocumentForm, DocumentProvisionForm
from .base import AbstractAuthedIndigoView


class DocumentDetailView(AbstractAuthedIndigoView, DetailView):
    model = Document
    context_object_name = 'document'
    pk_url_kwarg = 'doc_id'
    template_name = 'indigo_api/document/show.html'
    permission_required = ('indigo_api.view_document',)
    provision_eid = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # TODO: decide on cut-off size
        if len(self.object.document_xml) >= 5000000:
            # for large documents, redirect to the provision chooser to edit just a portion
            return redirect('choose_document_provision', doc_id=self.object.id)
        # otherwise, follow the normal get() path
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

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

        return context

    def get_document_content_json(self, document):
        return json.dumps(document.document_xml)


class ChooseDocumentProvisionView(AbstractAuthedIndigoView, DetailView, FormView):
    form_class = DocumentProvisionForm
    model = Document
    context_object_name = 'document'
    pk_url_kwarg = 'doc_id'
    template_name = 'indigo_api/document/_provisions.html'
    provision = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['provisions'] = self.get_shallow_toc(self.object.table_of_contents())
        context['country'] = self.object.work.country
        context['place'] = self.object.work.place
        context['work'] = self.object.work
        return context

    def get_shallow_toc(self, toc):
        # TODO: choose depth somehow; loading the whole thing can take ages
        #  -- or use htmx to only load children when selected?
        for e in toc:
            for c in e.children:
                for gc in c.children:
                    gc.children = []
        return toc

    def form_valid(self, form):
        self.provision = form.cleaned_data['provision']
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('document_provision', kwargs={'doc_id': int(self.kwargs['doc_id']), 'eid': self.provision})


class DocumentProvisionDetailView(DocumentDetailView):
    eid = None

    def get(self, request, *args, **kwargs):
        # don't call super(), we'll end up in a loop choosing a provision forever
        self.object = self.get_object()
        self.eid = self.kwargs.get('eid')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['provision_mode'] = self.eid is not None
        return context

    def get_document_content_json(self, document):
        component = document.doc.main
        elems = component.xpath(f".//a:*[@eId='{self.eid}']", namespaces={'a': self.object.doc.namespace})
        # TODO: throw a useful error including the eId if we don't have exactly one match
        assert len(elems) == 1

        return json.dumps(etree.tostring(elems[0], encoding='unicode'))


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
