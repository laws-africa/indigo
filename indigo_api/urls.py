from django.conf.urls import url, include
from django.views.decorators.cache import cache_page
from rest_framework.routers import DefaultRouter

import views.attachments
import views.countries
import views.documents
import views.misc
import views.public
import views.publications
import views.works


PUBLICATION_CACHE_SECS = 3600 * 24 * 30  # one month

router = DefaultRouter(trailing_slash=False)
router.register(r'documents', views.documents.DocumentViewSet, base_name='document')
router.register(r'documents/(?P<document_id>[0-9]+)/attachments', views.attachments.AttachmentViewSet, base_name='document-attachments')
router.register(r'documents/(?P<document_id>[0-9]+)/revisions', views.documents.RevisionViewSet, base_name='document-revisions')
router.register(r'documents/(?P<document_id>[0-9]+)/annotations', views.documents.AnnotationViewSet, base_name='document-annotations')
router.register(r'works', views.works.WorkViewSet, base_name='work')
router.register(r'works/(?P<work_id>[0-9]+)/amendments', views.works.WorkAmendmentViewSet, base_name='work-amendments')
router.register(r'countries', views.countries.CountryViewSet, base_name='country')

urlpatterns = [
    # --- public API ---
    # viewing a specific document identified by FRBR URI fragment,
    # this requires at least 4 components in the FRBR URI,
    # starting with the two-letter country code
    #
    # eg. /za/act/2007/98
    url(r'^(?P<frbr_uri>[a-z]{2}[-/].*)$',
        views.public.PublishedDocumentDetailView.as_view({'get': 'get'}),
        name='published-document-detail'),
    url(r'^search/(?P<country>[a-z]{2})$', views.public.PublishedDocumentSearchView.as_view(), name='public-search'),
    # --- END public API ---

    url(r'^search/documents$', views.documents.SearchView.as_view(), name='document-search'),
    url(r'^render$', views.documents.RenderView.as_view(), name='render'),
    url(r'^parse$', views.documents.ParseView.as_view(), name='parse'),
    url(r'^analysis/link-terms$', views.documents.LinkTermsView.as_view(), name='link-terms'),
    url(r'^analysis/link-references$', views.documents.LinkReferencesView.as_view(), name='link-references'),
    url(r'^publications/(?P<country>[a-z]{2})(-(?P<locality>[^/]+))?/find$',
        cache_page(PUBLICATION_CACHE_SECS)(views.publications.FindPublicationsView.as_view()), name='find-publications'),

    url(r'documents/(?P<document_id>[0-9]+)/media/(?P<filename>.*)$', views.attachments.attachment_media_view, name='document-media'),
    url(r'documents/(?P<document_id>[0-9]+)/activity', views.documents.DocumentActivityViewSet.as_view({
        'get': 'list', 'post': 'create', 'delete': 'destroy'}), name='document-activity'),

    url(r'^', include(router.urls)),
]
