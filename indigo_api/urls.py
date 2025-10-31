from django.urls import include, path, re_path
from django.views.decorators.cache import cache_control
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

urlpatterns = [
    re_path(r'^publications/(?P<country>[a-z]{2})(-(?P<locality>[^/]+))?/find$', publications.FindPublicationsView.as_view(), name='find-publications'),

    re_path(r'documents/(?P<document_id>[0-9]+)/media/(?P<filename>.*)$', attachments.AttachmentMediaView.as_view(), name='document-media'),
    path('documents/<int:document_id>/activity', documents.DocumentActivityViewSet.as_view({
        'get': 'list', 'post': 'create', 'delete': 'destroy'}), name='document-activity'),
    path('documents/<int:document_id>/diff', documents.DocumentDiffView.as_view(), name='document-diff'),
    path('documents/<int:document_id>/parse', documents.ParseView.as_view(), name='document-parse'),
    path('documents/<int:document_id>/render/coverpage', documents.RenderCoverpageView.as_view(), name='document-render-coverpage'),
    path('documents/<int:document_id>/static/<path:filename>', documents.StaticFinderView.as_view(), name='document-static-finder'),
    path('documents/<int:document_id>/analysis/link-terms', documents.LinkTermsView.as_view(), name='link-terms'),
    path('documents/<int:document_id>/analysis/link-references', documents.LinkReferencesView.as_view(), name='link-references'),
    path('documents/<int:document_id>/analysis/mark-up-italics', documents.MarkUpItalicsTermsView.as_view(), name='mark-up-italics'),
    path('documents/<int:document_id>/analysis/sentence-case-headings', documents.SentenceCaseHeadingsView.as_view(), name='sentence-case-headings'),

    path('documents/<int:document_id>/revisions/<int:pk>/diff', cache_control(public=True, max_age=24 * 3600)(documents.RevisionDiffView.as_view()), name='document-revisions-diff'),

    path('', include(router.urls)),
]
