from django.urls import include, path, re_path
from django.views.generic.base import RedirectView, TemplateView

from .views import users, works, documents, tasks, places, workflows, misc


urlpatterns = [
    # homepage
    path('', RedirectView.as_view(url='/places/', permanent=False)),
    # old permanent redirect
    path('library/', RedirectView.as_view(url='/places/', permanent=True)),

    # auth and accounts
    path('accounts/', include('allauth.urls')),
    path('accounts/profile/', users.EditAccountView.as_view(), name='edit_account'),
    path('accounts/profile/api/', users.EditAccountAPIView.as_view(), name='edit_account_api'),
    path('accounts/accept-terms', users.AcceptTermsView.as_view(), name='accept_terms'),

    path('terms', TemplateView.as_view(template_name='indigo_app/terms.html'), name='terms_of_use'),
    path('help', RedirectView.as_view(url='https://indigo.readthedocs.io/en/latest/', permanent=False), name='help'),

    path('places/', places.PlaceListView.as_view(), name='places'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/$', places.PlaceDetailView.as_view(), name='place'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/works/$', places.PlaceWorksView.as_view(), name='place_works'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/activity$', places.PlaceActivityView.as_view(), name='place_activity'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/metrics$', places.PlaceMetricsView.as_view(), name='place_metrics'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/settings', places.PlaceSettingsView.as_view(), name='place_settings'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/works/index.xlsx', places.PlaceWorksIndexView.as_view(), name='works_index'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/localities', places.PlaceLocalitiesView.as_view(), name='place_localities'),

    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/$', tasks.TaskListView.as_view(), name='tasks'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/new$', tasks.TaskCreateView.as_view(), name='create_task'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/update$', tasks.TaskBulkUpdateView.as_view(), name='bulk_task_update'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/$', tasks.TaskDetailView.as_view(), name='task_detail'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/edit$', tasks.TaskEditView.as_view(), name='task_edit'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/assign', tasks.TaskAssignView.as_view(), name='assign_task'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/unassign', tasks.TaskAssignView.as_view(unassign=True), name='unassign_task'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/projects', tasks.TaskChangeWorkflowsView.as_view(), name='task_workflows'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/block_by_task', tasks.TaskChangeBlockingTasksView.as_view(), name='task_blocked_by'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/submit', tasks.TaskChangeStateView.as_view(change='submit'), name='submit_task'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/cancel', tasks.TaskChangeStateView.as_view(change='cancel'), name='cancel_task'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/reopen', tasks.TaskChangeStateView.as_view(change='reopen'), name='reopen_task'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/unsubmit', tasks.TaskChangeStateView.as_view(change='unsubmit'), name='unsubmit_task'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/close', tasks.TaskChangeStateView.as_view(change='close'), name='close_task'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/block', tasks.TaskChangeStateView.as_view(change='block'), name='block_task'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/tasks/(?P<pk>\d+)/unblock', tasks.TaskChangeStateView.as_view(change='unblock'), name='unblock_task'),

    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/projects/$', workflows.WorkflowListView.as_view(), name='workflows'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/projects/new$', workflows.WorkflowCreateView.as_view(), name='workflow_create'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/projects/(?P<pk>\d+)/$', workflows.WorkflowDetailView.as_view(), name='workflow_detail'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/projects/(?P<pk>\d+)/edit$', workflows.WorkflowEditView.as_view(), name='workflow_edit'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/projects/(?P<pk>\d+)/tasks$', workflows.WorkflowAddTasksView.as_view(), name='workflow_add_tasks'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/projects/(?P<pk>\d+)/close$', workflows.WorkflowCloseView.as_view(), name='workflow_close'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/projects/(?P<pk>\d+)/reopen$', workflows.WorkflowReopenView.as_view(), name='workflow_reopen'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/projects/(?P<pk>\d+)/delete$', workflows.WorkflowDeleteView.as_view(), name='workflow_delete'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/projects/(?P<pk>\d+)/tasks/(?P<task_pk>\d+)/remove$', workflows.WorkflowRemoveTaskView.as_view(), name='workflow_remove_task'),

    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/works/new/$', works.AddWorkView.as_view(), name='new_work'),
    re_path(r'^places/(?P<place>[a-z]{2}(-[^/]+)?)/works/new-batch/$', works.BatchAddWorkView.as_view(), name='new_batch_work'),

    re_path(r'^works(?P<frbr_uri>/\S+?)/commencements/$', works.WorkCommencementsView.as_view(), name='work_commencements'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/commencements/new$', works.AddWorkCommencementView.as_view(), name='new_work_commencement'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/commencements/(?P<commencement_id>\d+)$', works.WorkCommencementUpdateView.as_view(), name='work_commencement_detail'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/commencements/uncommenced$', works.WorkUncommencedView.as_view(), name='work_uncommenced'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/$', works.WorkAmendmentsView.as_view(), name='work_amendments'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/new$', works.AddWorkAmendmentView.as_view(), name='new_work_amendment'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/arbitrary_expression_dates/new$', works.AddArbitraryExpressionDateView.as_view(), name='new_arbitrary_expression_date'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/arbitrary_expression_dates/(?P<arbitrary_expression_date_id>\d+)/edit$', works.EditArbitraryExpressionDateView.as_view(), name='edit_arbitrary_expression_date'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)$', works.WorkAmendmentDetailView.as_view(), name='work_amendment_detail'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/points-in-time/new$', works.AddWorkPointInTimeView.as_view(), name='new_work_point_in_time'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/popup$', works.WorkPopupView.as_view(), name='work_popup'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/related/$', works.WorkRelatedView.as_view(), name='work_related'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/import/$', works.ImportDocumentView.as_view(), name='import_document'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/edit/$', works.EditWorkView.as_view(), name='work_edit'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/delete$', works.DeleteWorkView.as_view(), name='work_delete'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/revisions/$', works.WorkVersionsView.as_view(), name='work_versions'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/tasks/$', works.WorkTasksView.as_view(), name='work_tasks'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/revisions/(?P<version_id>\d+)/restore$', works.RestoreWorkVersionView.as_view(), name='work_restore_version'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/media/publication/(?P<filename>.+)$', works.WorkPublicationDocumentView.as_view(), name='work_publication_document'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/$', works.WorkOverviewView.as_view(), name='work'),

    path('documents/<int:doc_id>/', documents.DocumentDetailView.as_view(), name='document'),
    path('documents/<int:doc_id>/popup', documents.DocumentPopupView.as_view(), name='document_popup'),

    path('tasks/', tasks.UserTasksView.as_view(), name='my_tasks'),
    path('tasks/available/', tasks.AvailableTasksView.as_view(), name='available_tasks'),
    path('tasks/priority/', tasks.AvailableTasksView.as_view(priority=True, tab='priority_tasks'), name='priority_tasks'),

    path('comments/', include('django_comments.urls')),
    path('jserror', misc.JSErrorView.as_view(), name='jserror'),

]
