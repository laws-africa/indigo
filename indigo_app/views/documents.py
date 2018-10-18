import json

from django.views.generic import DetailView
from django.http import Http404

from indigo_api.models import Document, Country, Subtype
from indigo_api.serializers import DocumentSerializer, WorkSerializer, WorkAmendmentSerializer

from indigo_app.forms import DocumentForm
from .base import AbstractAuthedIndigoView


class DocumentDetailView(AbstractAuthedIndigoView, DetailView):
    model = Document
    context_object_name = 'document'
    pk_url_kwarg = 'doc_id'
    template_name = 'document/show.html'

    # permissions
    permission_required = ('indigo_api.view_work',)

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
        context['locality'] = context['country'].work_locality(doc.work)

        # TODO do this in a better place
        context['countries'] = Country.objects.select_related('country').prefetch_related('localities', 'publication_set', 'country').all()
        context['countries_json'] = json.dumps({c.code: c.as_json() for c in context['countries']})

        context['document_content_json'] = json.dumps(doc.document_xml)

        context['amendments_json'] = json.dumps(
            WorkAmendmentSerializer(context={'request': self.request}, many=True)
            .to_representation(doc.work.amendments))

        context['form'] = DocumentForm(instance=doc)
        context['subtypes'] = Subtype.objects.order_by('name').all()

        return context
