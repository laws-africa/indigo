from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

import views.documents
import views.attachments
import views.works
import views.public
import views.misc

router = DefaultRouter(trailing_slash=False)
router.register(r'documents', views.documents.DocumentViewSet, base_name='document')
router.register(r'documents/(?P<document_id>[0-9]+)/attachments', views.attachments.AttachmentViewSet, base_name='document-attachments')
router.register(r'documents/(?P<document_id>[0-9]+)/revisions', views.documents.RevisionViewSet, base_name='document-revisions')
router.register(r'documents/(?P<document_id>[0-9]+)/annotations', views.documents.AnnotationViewSet, base_name='document-annotations')
router.register(r'works', views.works.WorkViewSet, base_name='work')
router.register(r'works/(?P<work_id>[0-9]+)/amendments', views.works.WorkAmendmentViewSet, base_name='work-amendments')

urlpatterns = [
    # viewing a specific document identified by FRBR URI fragment,
    # this requires at least 4 components in the FRBR URI,
    # starting with the two-letter country code
    #
    # eg. /za/act/2007/98
    url(r'^(?P<frbr_uri>[a-z]{2}[-/].*)$',
        views.public.PublishedDocumentDetailView.as_view({'get': 'get'}),
        name='published-document-detail'),

    url(r'^search/documents$', views.documents.SearchView.as_view(scope='documents'), name='search'),
    url(r'^search/works$', views.documents.SearchView.as_view(scope='works'), name='search'),
    url(r'^render$', views.documents.RenderView.as_view(), name='render'),
    url(r'^parse$', views.documents.ParseView.as_view(), name='parse'),
    url(r'^analysis/link-terms$', views.documents.LinkTermsView.as_view(), name='link-terms'),
    url(r'^analysis/link-references$', views.documents.LinkReferencesView.as_view(), name='link-references'),

    url(r'documents/(?P<document_id>[0-9]+)/media/(?P<filename>.*)$', views.attachments.attachment_media_view, name='document-media'),
    url(r'documents/(?P<document_id>[0-9]+)/activity', views.documents.DocumentActivityViewSet.as_view({
        'get': 'list', 'post': 'create', 'delete': 'destroy'}), name='document-activity'),

    # rest-based auth
    url(r'^auth/', include('rest_auth.urls')),
    url(r'^auth/new-token/$', views.misc.new_auth_token),

    url(r'^', include(router.urls)),
]
