from django.conf.urls import url, include
from django.views.generic.base import RedirectView, TemplateView

from .views import users, works, documents


urlpatterns = [
    # homepage
    url(r'^$', RedirectView.as_view(url='library', permanent=True)),

    # auth and accounts
    url(r'^accounts/', include('allauth.urls')),
    url(r'^accounts/profile/$', users.EditAccountView.as_view(), name='edit_account'),
    url(r'^accounts/profile/api/$', users.EditAccountAPIView.as_view(), name='edit_account_api'),
    url(r'^accounts/accept-terms$', users.AcceptTermsView.as_view(), name='accept_terms'),

    url(r'^terms', TemplateView.as_view(template_name='indigo_app/terms.html'), name='terms_of_use'),

    url(r'^works/new/$', works.AddWorkView.as_view(), name='new_work'),
    url(r'^works/new-batch/$', works.BatchAddWorkView.as_view(), name='new_batch_work'),
    url(r'^works(?P<frbr_uri>/\S+?)/amendments/$', works.WorkAmendmentsView.as_view(), name='work_amendments'),
    url(r'^works(?P<frbr_uri>/\S+?)/amendments/new$', works.AddWorkAmendmentView.as_view(), name='new_work_amendment'),
    url(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)$', works.WorkAmendmentDetailView.as_view(), name='work_amendment_detail'),
    url(r'^works(?P<frbr_uri>/\S+?)/points-in-time/new$', works.AddWorkPointInTimeView.as_view(), name='new_work_point_in_time'),
    url(r'^works(?P<frbr_uri>/\S+?)/related/$', works.WorkRelatedView.as_view(), name='work_related'),
    url(r'^works(?P<frbr_uri>/\S+?)/import/$', works.ImportDocumentView.as_view(), name='import_document'),
    url(r'^works(?P<frbr_uri>/\S+?)/edit/$', works.WorkDetailView.as_view(), name='work_edit'),
    url(r'^works(?P<frbr_uri>/\S+?)/revisions/$', works.WorkVersionsView.as_view(), name='work_versions'),
    url(r'^works(?P<frbr_uri>/\S+?)/revisions/(?P<version_id>\d+)/restore$', works.RestoreWorkVersionView.as_view(), name='work_restore_version'),
    url(r'^works(?P<frbr_uri>/\S+?)/$', works.WorkOverviewView.as_view(), name='work'),

    url(r'^documents/(?P<doc_id>\d+)/$', documents.DocumentDetailView.as_view(), name='document'),

    url(r'^library/$', works.LibraryView.as_view()),
    url(r'^library/(?P<country>[^\s/-]+)/$', works.LibraryView.as_view(), name='library'),
]
