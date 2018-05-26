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

    url(r'^documents/(?P<doc_id>\d+)/$', views.document, name='document'),
    url(r'^documents/new/$', views.document, name='new_document'),
    url(r'^documents/import/$', views.import_document, name='import_document'),
    url(r'^works/new/$', views.edit_work, name='new_work'),
    url(r'^works(?P<frbr_uri>/\S+?)/amendments/$', views.work_amendments, name='work_amendments'),
    url(r'^works(?P<frbr_uri>/\S+?)/related/$', views.work_related, name='work_related'),
    url(r'^works(?P<frbr_uri>/\S+?)/$', views.edit_work, name='work'),
    url(r'^library/$', views.library, name='library'),
]
