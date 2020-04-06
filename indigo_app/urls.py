from django.conf.urls import url, include
from django.views.generic.base import RedirectView, TemplateView

from .views import users, works, documents, tasks, places, workflows, misc


urlpatterns = [
    # homepage
    url(r'^$', RedirectView.as_view(url='/places/', permanent=False)),
    # old permanent redirect
    url(r'^library/$', RedirectView.as_view(url='/places/', permanent=True)),

    # auth and accounts
    url(r'^accounts/', include('allauth.urls')),
    url(r'^accounts/profile/$', users.EditAccountView.as_view(), name='edit_account'),
    url(r'^accounts/profile/api/$', users.EditAccountAPIView.as_view(), name='edit_account_api'),
    url(r'^accounts/accept-terms$', users.AcceptTermsView.as_view(), name='accept_terms'),

    url(r'^terms', TemplateView.as_view(template_name='indigo_app/terms.html'), name='terms_of_use'),
    url(r'^help', RedirectView.as_view(url='https://indigo.readthedocs.io/en/latest/', permanent=False), name='help'),

    url(r'^places/$', places.PlaceListView.as_view(), name='places'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/$', places.PlaceDetailView.as_view(), name='place'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/works/$', places.PlaceWorksView.as_view(), name='place_works'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/activity$', places.PlaceActivityView.as_view(), name='place_activity'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/metrics$', places.PlaceMetricsView.as_view(), name='place_metrics'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/settings', places.PlaceSettingsView.as_view(), name='place_settings'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/localities', places.PlaceLocalitiesView.as_view(), name='place_localities'),

    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/$', tasks.TaskListView.as_view(), name='tasks'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/new$', tasks.TaskCreateView.as_view(), name='create_task'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/update$', tasks.TaskBulkUpdateView.as_view(), name='bulk_task_update'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/$', tasks.TaskDetailView.as_view(), name='task_detail'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/edit$', tasks.TaskEditView.as_view(), name='task_edit'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/assign', tasks.TaskAssignView.as_view(), name='assign_task'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/unassign', tasks.TaskAssignView.as_view(unassign=True), name='unassign_task'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/workflows', tasks.TaskChangeWorkflowsView.as_view(), name='task_workflows'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/submit', tasks.TaskChangeStateView.as_view(change='submit'), name='submit_task'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/cancel', tasks.TaskChangeStateView.as_view(change='cancel'), name='cancel_task'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/reopen', tasks.TaskChangeStateView.as_view(change='reopen'), name='reopen_task'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/unsubmit', tasks.TaskChangeStateView.as_view(change='unsubmit'), name='unsubmit_task'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/close', tasks.TaskChangeStateView.as_view(change='close'), name='close_task'),

    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/workflows/$', workflows.WorkflowListView.as_view(), name='workflows'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/workflows/new$', workflows.WorkflowCreateView.as_view(), name='workflow_create'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/workflows/(?P<pk>\d+)/$', workflows.WorkflowDetailView.as_view(), name='workflow_detail'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/workflows/(?P<pk>\d+)/edit$', workflows.WorkflowEditView.as_view(), name='workflow_edit'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/workflows/(?P<pk>\d+)/tasks$', workflows.WorkflowAddTasksView.as_view(), name='workflow_add_tasks'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/workflows/(?P<pk>\d+)/close$', workflows.WorkflowCloseView.as_view(), name='workflow_close'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/workflows/(?P<pk>\d+)/reopen$', workflows.WorkflowReopenView.as_view(), name='workflow_reopen'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/workflows/(?P<pk>\d+)/delete$', workflows.WorkflowDeleteView.as_view(), name='workflow_delete'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/workflows/(?P<pk>\d+)/tasks/(?P<task_pk>\d+)/remove$', workflows.WorkflowRemoveTaskView.as_view(), name='workflow_remove_task'),

    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/works/new/$', works.AddWorkView.as_view(), name='new_work'),
    url(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/works/new-batch/$', works.BatchAddWorkView.as_view(), name='new_batch_work'),

    url(r'^works(?P<frbr_uri>/\S+?)/commencements/$', works.WorkCommencementsView.as_view(), name='work_commencements'),
    url(r'^works(?P<frbr_uri>/\S+?)/commencements/new$', works.AddWorkCommencementView.as_view(), name='new_work_commencement'),
    url(r'^works(?P<frbr_uri>/\S+?)/commencements/(?P<commencement_id>\d+)$', works.WorkCommencementUpdateView.as_view(), name='work_commencement_detail'),
    url(r'^works(?P<frbr_uri>/\S+?)/commencements/uncommenced$', works.WorkUncommencedView.as_view(), name='work_uncommenced'),
    url(r'^works(?P<frbr_uri>/\S+?)/amendments/$', works.WorkAmendmentsView.as_view(), name='work_amendments'),
    url(r'^works(?P<frbr_uri>/\S+?)/amendments/new$', works.AddWorkAmendmentView.as_view(), name='new_work_amendment'),
    url(r'^works(?P<frbr_uri>/\S+?)/arbitrary_expression_dates/new$', works.AddArbitraryExpressionDateView.as_view(), name='new_arbitrary_expression_date'),
    url(r'^works(?P<frbr_uri>/\S+?)/arbitrary_expression_dates/(?P<arbitrary_expression_date_id>\d+)/edit$', works.EditArbitraryExpressionDateView.as_view(), name='edit_arbitrary_expression_date'),
    url(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)$', works.WorkAmendmentDetailView.as_view(), name='work_amendment_detail'),
    url(r'^works(?P<frbr_uri>/\S+?)/points-in-time/new$', works.AddWorkPointInTimeView.as_view(), name='new_work_point_in_time'),
    url(r'^works(?P<frbr_uri>/\S+?)/popup$', works.WorkPopupView.as_view(), name='work_popup'),
    url(r'^works(?P<frbr_uri>/\S+?)/related/$', works.WorkRelatedView.as_view(), name='work_related'),
    url(r'^works(?P<frbr_uri>/\S+?)/import/$', works.ImportDocumentView.as_view(), name='import_document'),
    url(r'^works(?P<frbr_uri>/\S+?)/edit/$', works.EditWorkView.as_view(), name='work_edit'),
    url(r'^works(?P<frbr_uri>/\S+?)/delete$', works.DeleteWorkView.as_view(), name='work_delete'),
    url(r'^works(?P<frbr_uri>/\S+?)/revisions/$', works.WorkVersionsView.as_view(), name='work_versions'),
    url(r'^works(?P<frbr_uri>/\S+?)/tasks/$', works.WorkTasksView.as_view(), name='work_tasks'),
    url(r'^works(?P<frbr_uri>/\S+?)/revisions/(?P<version_id>\d+)/restore$', works.RestoreWorkVersionView.as_view(), name='work_restore_version'),
    url(r'^works(?P<frbr_uri>/\S+?)/media/publication/(?P<filename>.+)$', works.WorkPublicationDocumentView.as_view(), name='work_publication_document'),
    url(r'^works(?P<frbr_uri>/\S+?)/$', works.WorkOverviewView.as_view(), name='work'),

    url(r'^documents/(?P<doc_id>\d+)/$', documents.DocumentDetailView.as_view(), name='document'),
    url(r'^documents/(?P<doc_id>\d+)/popup$', documents.DocumentPopupView.as_view(), name='document_popup'),

    url(r'^tasks/$', tasks.UserTasksView.as_view(), name='my_tasks'),
    url(r'^tasks/available/$', tasks.AvailableTasksView.as_view(), name='available_tasks'),

    url(r'^comments/', include('django_comments.urls')),
    url(r'^jserror$', misc.JSErrorView.as_view(), name='jserror'),

]
