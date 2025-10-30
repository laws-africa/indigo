from django.urls import include, path, re_path
from django.views.generic.base import RedirectView, TemplateView
from django.views.decorators.cache import cache_page

from .views import users, works, documents, tasks, places


POPUP_CACHE_SECS = 60 * 30


urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),

    # homepage
    path('', RedirectView.as_view(url='/places', permanent=False)),

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

    path('places/<str:place>/works/actions', places.WorkActionsView.as_view(), name='place_works_actions'),
    path('places/<str:place>/works/update', places.WorkBulkUpdateView.as_view(), name='place_works_update'),
    path('places/<str:place>/works/approve', places.WorkBulkApproveView.as_view(), name='place_works_approve'),
    path('places/<str:place>/works/unapprove', places.WorkBulkUnapproveView.as_view(), name='place_works_unapprove'),
    path('places/<str:place>/works/link-references', places.WorkBulkLinkRefsView.as_view(), name='place_works_link_refs'),
    path('places/<str:place>/works/chooser', places.WorkChooserView.as_view(), name='place_work_chooser'),
    path('places/<str:place>/works/chooser/list', cache_page(30)(places.WorkChooserListView.as_view()), name='place_work_chooser_list'),
    path('places/<str:place>/works/detail/<int:pk>', places.WorkDetailView.as_view(), name='place_works_work_detail'),
    path('places/<str:place>/works/detail/<int:pk>/documents', places.WorkDocumentsView.as_view(), name='place_works_work_documents'),
    path('places/<str:place>/works/detail/<int:pk>/commencements', places.WorkCommencementsView.as_view(), name='place_works_work_commencements'),
    path('places/<str:place>/works/detail/<int:pk>/amendments', places.WorkAmendmentsView.as_view(), name='place_works_work_amendments'),
    path('places/<str:place>/works/detail/<int:pk>/repeals', places.WorkRepealsView.as_view(), name='place_works_work_repeals'),
    path('places/<str:place>/works/detail/<int:pk>/subsidiary', places.WorkSubsidiaryView.as_view(), name='place_works_work_subsidiary'),
    path('places/<str:place>/works/detail/<int:pk>/tasks', places.WorkTasksView.as_view(), name='place_works_work_tasks'),
    path('places/<str:place>/works/detail/<int:pk>/comments', places.WorkCommentsView.as_view(), name='place_works_work_comments'),

    path('places/<str:place>/activity', places.PlaceActivityView.as_view(), name='place_activity'),
    path('places/<str:place>/explorer', places.PlaceExplorerView.as_view(), name='place_explorer'),
    path('places/<str:place>/settings', places.PlaceSettingsView.as_view(), name='place_settings'),
    path('places/<str:place>/users', places.PlaceUsersView.as_view(), name='place_users'),
    path('places/<str:place>/works/index.xlsx', places.PlaceWorksIndexView.as_view(), name='works_index'),
    path('places/<str:place>/localities', places.PlaceLocalitiesView.as_view(), name='place_localities'),

    path('places/<str:place>/tasks', tasks.TaskListView.as_view(), name='tasks'),
    path('places/<str:place>/tasks/new', tasks.TaskCreateView.as_view(), name='create_task'),
    path('places/<str:place>/tasks/work-chooser', tasks.TaskWorkChooserView.as_view(), name='task_work_chooser'),
    path('places/<str:place>/tasks/form/work', tasks.TaskFormWorkView.as_view(), name='task_form_work'),
    path('places/<str:place>/tasks/form/title', tasks.TaskFormTitleView.as_view(), name='task_form_title'),
    path('places/<str:place>/tasks/form/timeline-date', tasks.TaskFormTimelineDateView.as_view(), name='task_form_timeline_date'),
    path('places/<str:place>/tasks/form/input-file', tasks.TaskFormInputFileView.as_view(), name='task_form_input_file'),
    path('places/<str:place>/tasks/form/output-file', tasks.TaskFormOutputFileView.as_view(), name='task_form_output_file'),
    path('places/<str:place>/tasks/update', tasks.TaskBulkUpdateView.as_view(), name='bulk_task_update'),
    path('places/<str:place>/tasks/unblock', tasks.TaskBulkChangeStateView.as_view(change='unblock'), name='bulk_task_unblock'),
    path('places/<str:place>/tasks/block', tasks.TaskBulkChangeStateView.as_view(change='block'), name='bulk_task_block'),
    path('places/<str:place>/tasks/assignees', tasks.TaskAssigneesView.as_view(), name='task_assignees_menu'),
    path('places/<str:place>/tasks/<int:pk>', tasks.TaskDetailView.as_view(), name='task_detail'),
    path('places/<str:place>/tasks/<int:pk>/detail', tasks.TaskDetailDetailView.as_view(), name='task_detail_detail'),
    path('places/<str:place>/tasks/<int:pk>/timeline', tasks.TaskTimelineView.as_view(), name='task_timeline'),
    path('places/<str:place>/tasks/<int:pk>/document-task-overview', tasks.DocumentTaskOverviewView.as_view(), name='document_task_overview'),
    path('places/<str:place>/tasks/<int:pk>/document-task-detail', tasks.DocumentTaskDetailView.as_view(), name='document_task_detail'),
    path('places/<str:place>/tasks/<int:pk>/edit', tasks.TaskEditView.as_view(), name='task_edit'),
    path('places/<str:place>/tasks/<int:pk>/annotation-anchor', tasks.TaskAnnotationAnchorView.as_view(), name='task_annotation_anchor'),
    path('places/<str:place>/tasks/<int:pk>/assign', tasks.TaskAssignView.as_view(), name='assign_task'),
    path('places/<str:place>/tasks/<int:pk>/assign-to', tasks.TaskAssignToView.as_view(), name='assign_task_to'),
    path('places/<str:place>/tasks/<int:pk>/unassign', tasks.TaskAssignView.as_view(unassign=True), name='unassign_task'),
    path('places/<str:place>/tasks/<int:pk>/blocking-tasks', tasks.TaskChangeBlockingTasksView.as_view(), name='task_blocked_by'),
    path('places/<str:place>/tasks/<int:pk>/submit', tasks.TaskChangeStateView.as_view(change='submit'), name='submit_task'),
    path('places/<str:place>/tasks/<int:pk>/finish', tasks.TaskChangeStateView.as_view(change='finish'), name='finish_task'),
    path('places/<str:place>/tasks/<int:pk>/cancel', tasks.TaskChangeStateView.as_view(change='cancel'), name='cancel_task'),
    path('places/<str:place>/tasks/<int:pk>/reopen', tasks.TaskChangeStateView.as_view(change='reopen'), name='reopen_task'),
    path('places/<str:place>/tasks/<int:pk>/unsubmit', tasks.TaskChangeStateView.as_view(change='unsubmit'), name='unsubmit_task'),
    path('places/<str:place>/tasks/<int:pk>/close', tasks.TaskChangeStateView.as_view(change='close'), name='close_task'),
    path('places/<str:place>/tasks/<int:pk>/block', tasks.TaskChangeStateView.as_view(change='block'), name='block_task'),
    path('places/<str:place>/tasks/<int:pk>/unblock', tasks.TaskChangeStateView.as_view(change='unblock'), name='unblock_task'),
    path('places/<str:place>/tasks/<int:pk>/edit-labels', tasks.TaskEditLabelsView.as_view(), name='task_labels'),
    path('places/<str:place>/tasks/<int:pk>/input-file', tasks.TaskFileView.as_view(task_file='input_file'), name='task_input_file'),
    path('places/<str:place>/tasks/<int:pk>/output-file', tasks.TaskFileView.as_view(task_file='output_file'), name='task_output_file'),

    path('places/<str:place>/works/new', works.AddWorkView.as_view(), name='new_work'),
    path('places/<str:place>/works/new-batch', works.BatchAddWorkView.as_view(), name='new_batch_work'),
    path('places/<str:place>/works/new-offcanvas', works.AddWorkOffCanvasView.as_view(), name='new_work_offcanvas'),
    path('places/<str:place>/works/update-batch', works.BatchUpdateWorkView.as_view(), name='update_batch_work'),

    # htmx partials for new and existing works
    path('places/<str:place>/work/form/find-duplicate', works.FindPossibleDuplicatesView.as_view(), name='work_form_find_duplicates'),
    path('places/<str:place>/work/form/find-publication', works.FindPublicationDocumentView.as_view(), name='work_form_find_publication_document'),
    path('places/<str:place>/work/form/attach-publication', works.WorkFormPublicationDocumentView.as_view(), name='work_form_attach_publication_document'),
    path('places/<str:place>/work/form/localities', works.WorkFormLocalityView.as_view(), name='work_form_locality'),
    path('places/<str:place>/work/form/repeal', works.WorkFormRepealView.as_view(), name='work_form_repeal'),
    path('places/<str:place>/work/form/parent', works.WorkFormParentView.as_view(), name='work_form_parent'),

    re_path(r'^works(?P<frbr_uri>/\S+?)/form/repeals-made$', works.WorkFormRepealsMadeView.as_view(), name='work_form_repeals_made'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/form/chapter-numbers$', works.WorkFormChapterNumbersView.as_view(), name='work_form_chapter_numbers'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/form/amendments$', works.WorkFormAmendmentsView.as_view(), name='work_form_amendments'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/form/commencements$', works.WorkFormCommencementsView.as_view(), name='work_form_commencements'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/form/commencements-made$', works.WorkFormCommencementsMadeView.as_view(), name='work_form_commencements_made'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/form/conslidations$', works.WorkFormConsolidationView.as_view(), name='work_form_consolidation'),

    re_path(r'^works(?P<frbr_uri>/\S+?)/commencements/$', works.WorkCommencementsView.as_view(), name='work_commencements'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/commencements/uncommenced-provisions$', works.WorkUncommencedProvisionsDetailView.as_view(), name='work_uncommenced_provisions'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/commencements/new$', works.WorkCommencementAddView.as_view(), name='work_commencement_add'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/commencements/(?P<pk>\d+)$', works.WorkCommencementDetailView.as_view(), name='work_commencement_detail'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/commencements/(?P<pk>\d+)/provisions-detail$', works.WorkCommencementProvisionsDetailView.as_view(), name='work_commencement_provisions_detail'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/commencements/(?P<pk>\d+)/edit$', works.WorkCommencementEditView.as_view(), name='work_commencement_edit'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/commencements/(?P<pk>\d+)/commencing-work-edit$', works.WorkCommencementCommencingWorkEditView.as_view(), name='work_commencement_commencing_work_edit'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/commencements/(?P<pk>\d+)/provisions-edit$', works.WorkCommencementProvisionsEditView.as_view(), name='work_commencement_provisions_edit'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/commencements/uncommenced$', works.WorkUncommencedView.as_view(), name='work_uncommenced'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/$', works.WorkAmendmentsView.as_view(), name='work_amendments'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/new$', works.AddWorkAmendmentView.as_view(), name='new_work_amendment'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/arbitrary_expression_dates/new$', works.AddArbitraryExpressionDateView.as_view(), name='new_arbitrary_expression_date'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/arbitrary_expression_dates/(?P<arbitrary_expression_date_id>\d+)/edit$', works.EditArbitraryExpressionDateView.as_view(), name='edit_arbitrary_expression_date'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)$', works.WorkAmendmentUpdateView.as_view(), name='work_amendment_detail'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)/dropdown$', works.WorkAmendmentDropdownView.as_view(), name='work_amendment_dropdown'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/points-in-time/new$', works.AddWorkPointInTimeView.as_view(), name='new_work_point_in_time'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/popup$', cache_page(POPUP_CACHE_SECS)(works.WorkPopupView.as_view()), name='work_popup'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/related/$', works.WorkRelatedView.as_view(), name='work_related'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/import/$', works.ImportDocumentView.as_view(), name='import_document'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/edit/$', works.EditWorkView.as_view(), name='work_edit'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/unapprove$', works.UnapproveWorkView.as_view(), name='work_unapprove'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/edit-offcanvas$', works.EditWorkOffCanvasView.as_view(), name='work_edit_offcanvas'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/list-item$', works.WorkListItemPartialView.as_view(), name='work_list_item'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/delete$', works.DeleteWorkView.as_view(), name='work_delete'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/revisions/$', works.WorkVersionsView.as_view(), name='work_versions'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/tasks/$', works.WorkTasksView.as_view(), name='work_tasks'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/revisions/(?P<version_id>\d+)/restore$', works.RestoreWorkVersionView.as_view(), name='work_restore_version'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/media/publication/(?P<filename>.+)$', works.WorkPublicationDocumentView.as_view(), name='work_publication_document'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/$', works.WorkOverviewView.as_view(), name='work'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/comments$', works.WorkCommentsView.as_view(), name='work_comments'),

    path('documents/<int:doc_id>/', documents.DocumentDetailView.as_view(), name='document'),
    path('documents/<int:doc_id>/choose-provision', documents.ChooseDocumentProvisionView.as_view(), name='choose_document_provision'),
    path('documents/<int:doc_id>/popup', cache_page(POPUP_CACHE_SECS)(documents.DocumentPopupView.as_view()), name='document_popup'),
    path('documents/<int:doc_id>/provision/<str:eid>', documents.DocumentProvisionDetailView.as_view(), name='document_provision'),

    path('tasks/', tasks.UserTasksView.as_view(), name='my_tasks'),
    path('tasks/all/', tasks.AllTasksView.as_view(), name='all_tasks'),

    path('comments/', include('django_comments.urls')),

]
