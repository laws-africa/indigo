from django.urls import re_path

from bluebell_migration import views


urlpatterns = [
    re_path(r'^works(?P<frbr_uri>/\S+?)/bb-migration/$', views.WorkViewBluebellMigration.as_view(), name='bb_migrate_work'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/bb-migration/(?P<doc_id>\d+)/$', views.DocumentViewBluebellMigration.as_view(), name='bb_migrate_document'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/bl-migration/(?P<doc_id>\d+)/$', views.DocumentViewBluebellMigrationBl.as_view(), name='bl_migrate_document'),
]
