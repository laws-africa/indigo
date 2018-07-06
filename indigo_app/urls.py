from django.conf.urls import url
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    # auth
    url('^user/login/$', auth_views.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    url('^user/password-reset/$', auth_views.PasswordResetView.as_view(), name='password_reset'),
    url('^user/password-reset/sent/$', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    url('^user/password-reset/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    url('^user/password-reset/complete/$', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # homepage
    url(r'^$', RedirectView.as_view(url='library', permanent=True)),

    url(r'^works/new/$', views.AddWorkView.as_view(), name='new_work'),
    url(r'^works(?P<frbr_uri>/\S+?)/amendments/$', views.WorkAmendmentsView.as_view(), name='work_amendments'),
    url(r'^works(?P<frbr_uri>/\S+?)/related/$', views.WorkRelatedView.as_view(), name='work_related'),
    url(r'^works(?P<frbr_uri>/\S+?)/$', views.WorkDetailView.as_view(), name='work'),

    url(r'^documents/(?P<doc_id>\d+)/$', views.DocumentDetailView.as_view(), name='document'),
    url(r'^documents/import/$', views.ImportDocumentView.as_view(), name='import_document'),

    url(r'^library/$', views.LibraryView.as_view()),
    url(r'^library/(?P<country>[^\s/-]+)/$', views.LibraryView.as_view(), name='library'),
]
