from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

import indigo_api.views.attachments as attachments
import indigo_api.views.documents as documents
import indigo_api.views.publications as publications
import indigo_api.views.works as works


router = DefaultRouter(trailing_slash=False)
router.register(r'documents', documents.DocumentViewSet, basename='document')
router.register(r'documents/(?P<document_id>[0-9]+)/attachments', attachments.AttachmentViewSet, basename='document-attachments')
router.register(r'documents/(?P<document_id>[0-9]+)/revisions', documents.RevisionViewSet, basename='document-revisions')
router.register(r'documents/(?P<document_id>[0-9]+)/annotations', documents.AnnotationViewSet, basename='document-annotations')
router.register(r'works', works.WorkViewSet, basename='work')
router.register(r'works/(?P<work_id>[0-9]+)/amendments', works.WorkAmendmentViewSet, basename='work-amendments')

urlpatterns = [
    path('search/documents', documents.SearchView.as_view(), name='document-search'),
    path('render', documents.RenderView.as_view(), name='render'),
    path('render/coverpage', documents.RenderView.as_view(coverpage_only=True), name='render'),
    path('parse', documents.ParseView.as_view(), name='parse'),
    path('analysis/link-terms', documents.LinkTermsView.as_view(), name='link-terms'),
    path('analysis/link-references', documents.LinkReferencesView.as_view(), name='link-references'),
    path('analysis/mark-up-italics', documents.MarkUpItalicsTermsView.as_view(), name='mark-up-italics'),
    re_path(r'^publications/(?P<country>[a-z]{2})(-(?P<locality>[^/]+))?/find$', publications.FindPublicationsView.as_view(), name='find-publications'),

    re_path(r'documents/(?P<document_id>[0-9]+)/media/(?P<filename>.*)$', attachments.AttachmentMediaView.as_view(), name='document-media'),
    path('documents/<int:document_id>/activity', documents.DocumentActivityViewSet.as_view({
        'get': 'list', 'post': 'create', 'delete': 'destroy'}), name='document-activity'),
    path('documents/<int:document_id>/diff', documents.DocumentDiffView.as_view(), name='document-diff'),

    path('', include(router.urls)),
]
