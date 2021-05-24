import json

from django.views.generic import DetailView
from django.http import Http404
from django.urls import reverse

from indigo.plugins import plugins
from indigo_api.models import Document, Country, Subtype, Work, TaxonomyVocabulary
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
        doc = super(DocumentDetailView, self).get_object(queryset)
        if doc.deleted:
            raise Http404()
        return doc

    def get_context_data(self, **kwargs):
        context = super(DocumentDetailView, self).get_context_data(**kwargs)

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
        context['taxonomies'] = TaxonomyVocabulary.objects.all()

        context['document_content_json'] = json.dumps(doc.document_xml)

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
