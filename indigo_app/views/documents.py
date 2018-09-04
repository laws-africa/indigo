import json

from django.views.generic import DetailView
from django.http import Http404

from indigo_api.models import Document, Work, Language, Country, Subtype
from indigo_api.serializers import DocumentSerializer, WorkSerializer, WorkAmendmentSerializer
from indigo_api.views.documents import DocumentViewSet

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

        context['work'] = doc.work
        context['work_json'] = json.dumps(WorkSerializer(instance=doc.work, context={'request': self.request}).data)
        context['country'] = doc.work.country
        context['locality'] = context['country'].work_locality(doc.work)

        # TODO do this in a better place
        context['countries'] = Country.objects.select_related('country').prefetch_related('locality_set', 'publication_set', 'country').all()
        context['countries_json'] = json.dumps({c.code: c.as_json() for c in context['countries']})

        context['document_content_json'] = json.dumps(doc.document_xml)

        serializer = WorkSerializer(context={'request': self.request}, many=True)
        works = Work.objects.filter(country=doc.work.country)
        context['works_json'] = json.dumps(serializer.to_representation(works))

        context['amendments_json'] = json.dumps(
            WorkAmendmentSerializer(context={'request': self.request}, many=True)
            .to_representation(doc.work.amendments))

        context['form'] = DocumentForm(instance=doc)
        context['countries'] = Country.objects.select_related('country').prefetch_related('locality_set', 'publication_set', 'country').all()
        context['countries_json'] = json.dumps({c.code: c.as_json() for c in context['countries']})
        context['subtypes'] = Subtype.objects.order_by('name').all()
        context['languages'] = Language.objects.select_related('language').all()

        serializer = DocumentSerializer(context={'request': self.request}, many=True)
        context['documents_json'] = json.dumps(serializer.to_representation(DocumentViewSet.queryset.all()))
        return context
