import json

from django.views.generic import DetailView
from django.http import Http404
from django.urls import reverse

from indigo_api.models import Document, Country, Subtype
from indigo_api.serializers import DocumentSerializer, WorkSerializer, WorkAmendmentSerializer
from indigo_api.views.documents import DocumentViewSet

from indigo_app.forms import DocumentForm
from .base import AbstractAuthedIndigoView


class DocumentDetailView(AbstractAuthedIndigoView, DetailView):
    model = Document
    context_object_name = 'document'
    pk_url_kwarg = 'doc_id'
    template_name = 'document/show.html'

    def get_object(self, queryset=None):
        doc = super(DocumentDetailView, self).get_object(queryset)
        if doc.deleted:
            raise Http404()
        return doc

    def get_context_data(self, **kwargs):
        context = super(DocumentDetailView, self).get_context_data(**kwargs)

        doc = self.object

        context['work_json'] = json.dumps(WorkSerializer(instance=doc.work, context={'request': self.request}).data)
        context['work'] = doc.work
        context['work_json'] = json.dumps(WorkSerializer(instance=doc.work, context={'request': self.request}).data)
        context['document_json'] = json.dumps(DocumentSerializer(instance=doc, context={'request': self.request}).data)
        # expressions
        context['expressions_json'] = json.dumps(
            DocumentSerializer(context={'request': self.request}, many=True)
            .to_representation(
                doc.work.expressions().all()
            ))
        context['country'] = doc.work.country
        context['locality'] = doc.work.locality

        # TODO do this in a better place
        context['countries'] = Country.objects.select_related('country').prefetch_related('localities', 'publication_set', 'country').all()

        context['document_content_json'] = json.dumps(doc.document_xml)

        context['amendments_json'] = json.dumps(
            WorkAmendmentSerializer(context={'request': self.request}, many=True)
            .to_representation(doc.work.amendments))

        context['form'] = DocumentForm(instance=doc)
        context['subtypes'] = Subtype.objects.order_by('name').all()

        context['download_formats'] = [{
            'url': reverse('document-detail', kwargs={'pk': doc.id, 'format': r.format}) + getattr(r, 'suffix', ''),
            'icon': r.icon,
            'title': r.title
        } for r in DocumentViewSet.renderer_classes if hasattr(r, 'icon')]
        context['download_formats'].sort(key=lambda f: f['title'])

        return context

class DocumentPopupView(AbstractAuthedIndigoView, DetailView):
    model = Document
    context_object_name = 'document'
    pk_url_kwarg = 'doc_id'
    template_name = 'indigo_api/document_popup.html'

    def get_object(self, queryset=None):
        doc = super(DocumentPopupView, self).get_object(queryset)
        if doc.deleted:
            raise Http404()
        return doc
