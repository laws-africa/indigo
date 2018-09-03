from django.conf.urls import url, include
from django.views.generic.base import RedirectView, TemplateView

from . import views


urlpatterns = [
    # homepage
    url(r'^$', RedirectView.as_view(url='library', permanent=True)),

    # auth and accounts
    url(r'^accounts/', include('allauth.urls')),
    url(r'^accounts/profile/$', views.EditAccountView.as_view(), name='edit_account'),
    url(r'^accounts/profile/api/$', views.EditAccountAPIView.as_view(), name='edit_account_api'),
    url(r'^accounts/accept-terms$', views.AcceptTermsView.as_view(), name='accept_terms'),

    url(r'^terms', TemplateView.as_view(template_name='indigo_app/terms.html'), name='terms_of_use'),

    url(r'^works/new/$', views.AddWorkView.as_view(), name='new_work'),
    url(r'^works/new-batch/$', views.BatchAddWorkView.as_view(), name='new_batch_work'),
    url(r'^works(?P<frbr_uri>/\S+?)/amendments/$', views.WorkAmendmentsView.as_view(), name='work_amendments'),
    url(r'^works(?P<frbr_uri>/\S+?)/amendments/new$', views.AddWorkAmendmentView.as_view(), name='new_work_amendment'),
    url(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)$', views.WorkAmendmentDetailView.as_view(), name='work_amendment_detail'),
    url(r'^works(?P<frbr_uri>/\S+?)/related/$', views.WorkRelatedView.as_view(), name='work_related'),
    url(r'^works(?P<frbr_uri>/\S+?)/import/$', views.ImportDocumentView.as_view(), name='import_document'),
    url(r'^works(?P<frbr_uri>/\S+?)/edit/$', views.WorkDetailView.as_view(), name='work_edit'),
    url(r'^works(?P<frbr_uri>/\S+?)/revisions/$', views.WorkVersionsView.as_view(), name='work_versions'),
    url(r'^works(?P<frbr_uri>/\S+?)/revisions/(?P<version_id>\d+)/restore$', views.RestoreWorkVersionView.as_view(), name='work_restore_version'),
    url(r'^works(?P<frbr_uri>/\S+?)/$', views.WorkOverviewView.as_view(), name='work'),

    url(r'^documents/(?P<doc_id>\d+)/$', views.DocumentDetailView.as_view(), name='document'),

    url(r'^library/$', views.LibraryView.as_view()),
    url(r'^library/(?P<country>[^\s/-]+)/$', views.LibraryView.as_view(), name='library'),
]
