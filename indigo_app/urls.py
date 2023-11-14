from django.urls import include, path, re_path
from django.views.generic.base import RedirectView, TemplateView

from .views import users, works, documents, tasks, places, workflows


urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),

    # homepage
    path('', RedirectView.as_view(url='/places/', permanent=False)),

    # auth and accounts
    path('accounts/', include('allauth.urls')),
    path('accounts/profile/', users.EditAccountView.as_view(), name='edit_account'),
    path('accounts/profile/api/', users.EditAccountAPIView.as_view(), name='edit_account_api'),
    path('accounts/accept-terms', users.AcceptTermsView.as_view(), name='accept_terms'),

    path('terms', TemplateView.as_view(template_name='indigo_app/terms.html'), name='terms_of_use'),
    path('help', RedirectView.as_view(url='https://indigo.readthedocs.io/en/latest/', permanent=False), name='help'),

    path('places', places.PlaceListView.as_view(), name='places'),
    path('places/<str:place>', places.PlaceDetailView.as_view(), name='place'),
    path('places/<str:place>/works', places.PlaceWorksView.as_view(), name='place_works'),

    path('places/<str:place>/works2', places.PlaceWorksView2.as_view(), name='place_works2'),
    path('places/<str:place>/works/facets', places.PlaceWorksFacetsView.as_view(), name='place_works_facets'),
    path('places/<str:place>/works/actions', places.WorkActionsView.as_view(), name='place_works_actions'),
    path('places/<str:place>/works/detail/<int:pk>', places.WorkDetailView.as_view(), name='place_works_work_detail'),
    path('places/<str:place>/works/detail/<int:pk>/commencements', places.WorkCommencementsView.as_view(), name='place_works_work_commencements'),
    path('places/<str:place>/works/detail/<int:pk>/amendments', places.WorkAmendmentsView.as_view(), name='place_works_work_amendments'),
    path('places/<str:place>/works/detail/<int:pk>/repeals', places.WorkRepealsView.as_view(), name='place_works_work_repeals'),
    path('places/<str:place>/works/detail/<int:pk>/subsidiary', places.WorkSubsidiaryView.as_view(), name='place_works_work_subsidiary'),

    path('places/<str:place>/activity', places.PlaceActivityView.as_view(), name='place_activity'),
    path('places/<str:place>/metrics', places.PlaceMetricsView.as_view(), name='place_metrics'),
    path('places/<str:place>/explorer', places.PlaceExplorerView.as_view(), name='place_explorer'),
    path('places/<str:place>/settings', places.PlaceSettingsView.as_view(), name='place_settings'),
    path('places/<str:place>/users', places.PlaceUsersView.as_view(), name='place_users'),
    path('places/<str:place>/works/index.xlsx', places.PlaceWorksIndexView.as_view(), name='works_index'),
    path('places/<str:place>/localities', places.PlaceLocalitiesView.as_view(), name='place_localities'),

    path('places/<str:place>/tasks', tasks.TaskListView.as_view(), name='tasks'),
    path('places/<str:place>/tasks/new', tasks.TaskCreateView.as_view(), name='create_task'),
    path('places/<str:place>/tasks/update', tasks.TaskBulkUpdateView.as_view(), name='bulk_task_update'),
    path('places/<str:place>/tasks/assignees', tasks.TaskAssigneesView.as_view(), name='task_assignees_menu'),
    path('places/<str:place>/tasks/<int:pk>', tasks.TaskDetailView.as_view(), name='task_detail'),
    path('places/<str:place>/tasks/<int:pk>/edit', tasks.TaskEditView.as_view(), name='task_edit'),
    path('places/<str:place>/tasks/<int:pk>/assign', tasks.TaskAssignView.as_view(), name='assign_task'),
    path('places/<str:place>/tasks/<int:pk>/unassign', tasks.TaskAssignView.as_view(unassign=True), name='unassign_task'),
    path('places/<str:place>/tasks/<int:pk>/projects', tasks.TaskChangeWorkflowsView.as_view(), name='task_workflows'),
    path('places/<str:place>/tasks/<int:pk>/blocking-tasks', tasks.TaskChangeBlockingTasksView.as_view(), name='task_blocked_by'),
    path('places/<str:place>/tasks/<int:pk>/submit', tasks.TaskChangeStateView.as_view(change='submit'), name='submit_task'),
    path('places/<str:place>/tasks/<int:pk>/cancel', tasks.TaskChangeStateView.as_view(change='cancel'), name='cancel_task'),
    path('places/<str:place>/tasks/<int:pk>/reopen', tasks.TaskChangeStateView.as_view(change='reopen'), name='reopen_task'),
    path('places/<str:place>/tasks/<int:pk>/unsubmit', tasks.TaskChangeStateView.as_view(change='unsubmit'), name='unsubmit_task'),
    path('places/<str:place>/tasks/<int:pk>/close', tasks.TaskChangeStateView.as_view(change='close'), name='close_task'),
    path('places/<str:place>/tasks/<int:pk>/block', tasks.TaskChangeStateView.as_view(change='block'), name='block_task'),
    path('places/<str:place>/tasks/<int:pk>/unblock', tasks.TaskChangeStateView.as_view(change='unblock'), name='unblock_task'),

    path('places/<str:place>/projects', workflows.WorkflowListView.as_view(), name='workflows'),
    path('places/<str:place>/projects/new', workflows.WorkflowCreateView.as_view(), name='workflow_create'),
    path('places/<str:place>/projects/<int:pk>', workflows.WorkflowDetailView.as_view(), name='workflow_detail'),
    path('places/<str:place>/projects/<int:pk>/edit', workflows.WorkflowEditView.as_view(), name='workflow_edit'),
    path('places/<str:place>/projects/<int:pk>/tasks', workflows.WorkflowAddTasksView.as_view(), name='workflow_add_tasks'),
    path('places/<str:place>/projects/<int:pk>/close', workflows.WorkflowCloseView.as_view(), name='workflow_close'),
    path('places/<str:place>/projects/<int:pk>/reopen', workflows.WorkflowReopenView.as_view(), name='workflow_reopen'),
    path('places/<str:place>/projects/<int:pk>/delete', workflows.WorkflowDeleteView.as_view(), name='workflow_delete'),
    path('places/<str:place>/projects/<int:pk>/tasks/<int:task_pk>/remove', workflows.WorkflowRemoveTaskView.as_view(), name='workflow_remove_task'),

    path('places/<str:place>/works/new', works.AddWorkView.as_view(), name='new_work'),
    path('places/<str:place>/works/new-batch', works.BatchAddWorkView.as_view(), name='new_batch_work'),
    path('places/<str:place>/works/update-batch', works.BatchUpdateWorkView.as_view(), name='update_batch_work'),

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
    path('tasks/topic/', tasks.TaxonomyTopicTaskListView.as_view(), name='taxonomy_task_list'),
    path('tasks/topic/<slug:slug>/', tasks.TaxonomyTopicTaskDetailView.as_view(), name='taxonomy_task_detail'),
    path('tasks/available/', tasks.AvailableTasksView.as_view(), name='available_tasks'),
    path('tasks/priority/', tasks.AvailableTasksView.as_view(priority=True, tab='priority_tasks'), name='priority_tasks'),

    path('comments/', include('django_comments.urls')),

]
