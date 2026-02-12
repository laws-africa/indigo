from django.urls import include, path, re_path
from django.views.generic.base import RedirectView, TemplateView
from django.views.decorators.cache import cache_page

from .views import users, works, documents, tasks, places, amendments


POPUP_CACHE_SECS = 60 * 30


urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),

    # homepage
    path('', RedirectView.as_view(url='/places', permanent=False)),

    # auth and accounts
    path('accounts/', include([
        path('', include('allauth.urls')),
        path('profile/', users.EditAccountView.as_view(), name='edit_account'),
        path('profile/api/', users.EditAccountAPIView.as_view(), name='edit_account_api'),
        path('accept-terms', users.AcceptTermsView.as_view(), name='accept_terms'),
    ])),

    path('terms', TemplateView.as_view(template_name='indigo_app/terms.html'), name='terms_of_use'),
    path('help', RedirectView.as_view(url='https://indigo.readthedocs.io/en/latest/', permanent=False), name='help'),
    re_path('^(?P<frbr_uri>akn/.+)$', works.AknResolverView.as_view(), name='akn_resolver'),

    path('places', include([
        path('', places.PlaceListView.as_view(), name='places'),
        path('/<str:place>', include([
            path('', places.PlaceDetailView.as_view(), name='place'),
            path('/works', include([
                path('', places.PlaceWorksView.as_view(), name='place_works'),
                path('/index.xlsx', places.PlaceWorksIndexView.as_view(), name='works_index'),
                path('/actions', places.WorkActionsView.as_view(), name='place_works_actions'),
                path('/update', places.WorkBulkUpdateView.as_view(), name='place_works_update'),
                path('/approve', places.WorkBulkApproveView.as_view(), name='place_works_approve'),
                path('/unapprove', places.WorkBulkUnapproveView.as_view(), name='place_works_unapprove'),
                path('/link-references', places.WorkBulkLinkRefsView.as_view(), name='place_works_link_refs'),
                path('/new', works.AddWorkView.as_view(), name='new_work'),
                path('/new-batch', works.BatchAddWorkView.as_view(), name='new_batch_work'),
                path('/new-offcanvas', works.AddWorkOffCanvasView.as_view(), name='new_work_offcanvas'),
                path('/update-batch', works.BatchUpdateWorkView.as_view(), name='update_batch_work'),
                path('//chooser', places.WorkChooserView.as_view(), name='place_work_chooser'),
                path('/chooser/list', cache_page(30)(places.WorkChooserListView.as_view()), name='place_work_chooser_list'),
                path('/detail/<int:pk>', include([
                    path('', places.WorkDetailView.as_view(), name='place_works_work_detail'),
                    path('/documents', places.WorkDocumentsView.as_view(), name='place_works_work_documents'),
                    path('/commencements', places.WorkCommencementsView.as_view(), name='place_works_work_commencements'),
                    path('/amendments', places.WorkAmendmentsView.as_view(), name='place_works_work_amendments'),
                    path('/repeals', places.WorkRepealsView.as_view(), name='place_works_work_repeals'),
                    path('/subsidiary', places.WorkSubsidiaryView.as_view(), name='place_works_work_subsidiary'),
                    path('/tasks', places.WorkTasksView.as_view(), name='place_works_work_tasks'),
                    path('/comments', places.WorkCommentsView.as_view(), name='place_works_work_comments'),
                ])),
            ])),
            path('/activity', places.PlaceActivityView.as_view(), name='place_activity'),
            path('/explorer', places.PlaceExplorerView.as_view(), name='place_explorer'),
            path('/settings', places.PlaceSettingsView.as_view(), name='place_settings'),
            path('/users', places.PlaceUsersView.as_view(), name='place_users'),
            path('/localities', places.PlaceLocalitiesView.as_view(), name='place_localities'),
            path('/tasks', include([
                path('', tasks.TaskListView.as_view(), name='tasks'),
                path('/new', tasks.TaskCreateView.as_view(), name='create_task'),
                path('/work-chooser', tasks.TaskWorkChooserView.as_view(), name='task_work_chooser'),
                path('/form/work', tasks.TaskFormWorkView.as_view(), name='task_form_work'),
                path('/form/title', tasks.TaskFormTitleView.as_view(), name='task_form_title'),
                path('/form/timeline-date', tasks.TaskFormTimelineDateView.as_view(), name='task_form_timeline_date'),
                path('/form/input-file', tasks.TaskFormInputFileView.as_view(), name='task_form_input_file'),
                path('/form/output-file', tasks.TaskFormOutputFileView.as_view(), name='task_form_output_file'),
                path('/update', tasks.TaskBulkUpdateView.as_view(), name='bulk_task_update'),
                path('/unblock', tasks.TaskBulkChangeStateView.as_view(change='unblock'), name='bulk_task_unblock'),
                path('/block', tasks.TaskBulkChangeStateView.as_view(change='block'), name='bulk_task_block'),
                path('/assignees', tasks.TaskAssigneesView.as_view(), name='task_assignees_menu'),
                path('/<int:pk>', include([
                    path('', tasks.TaskDetailView.as_view(), name='task_detail'),
                    path('/detail', tasks.TaskDetailDetailView.as_view(), name='task_detail_detail'),
                    path('/timeline', tasks.TaskTimelineView.as_view(), name='task_timeline'),
                    path('/document-task-overview', tasks.DocumentTaskOverviewView.as_view(), name='document_task_overview'),
                    path('/document-task-detail', tasks.DocumentTaskDetailView.as_view(), name='document_task_detail'),
                    path('/edit', tasks.TaskEditView.as_view(), name='task_edit'),
                    path('/annotation-anchor', tasks.TaskAnnotationAnchorView.as_view(), name='task_annotation_anchor'),
                    path('/assign', tasks.TaskAssignView.as_view(), name='assign_task'),
                    path('/assign-to', tasks.TaskAssignToView.as_view(), name='assign_task_to'),
                    path('/unassign', tasks.TaskAssignView.as_view(unassign=True), name='unassign_task'),
                    path('/blocking-tasks', tasks.TaskChangeBlockingTasksView.as_view(), name='task_blocked_by'),
                    path('/submit', tasks.TaskChangeStateView.as_view(change='submit'), name='submit_task'),
                    path('/finish', tasks.TaskChangeStateView.as_view(change='finish'), name='finish_task'),
                    path('/cancel', tasks.TaskChangeStateView.as_view(change='cancel'), name='cancel_task'),
                    path('/reopen', tasks.TaskChangeStateView.as_view(change='reopen'), name='reopen_task'),
                    path('/unsubmit', tasks.TaskChangeStateView.as_view(change='unsubmit'), name='unsubmit_task'),
                    path('/close', tasks.TaskChangeStateView.as_view(change='close'), name='close_task'),
                    path('/block', tasks.TaskChangeStateView.as_view(change='block'), name='block_task'),
                    path('/unblock', tasks.TaskChangeStateView.as_view(change='unblock'), name='unblock_task'),
                    path('/edit-labels', tasks.TaskEditLabelsView.as_view(), name='task_labels'),
                    path('/input-file', tasks.TaskFileView.as_view(task_file='input_file'), name='task_input_file'),
                    path('/output-file', tasks.TaskFileView.as_view(task_file='output_file'), name='task_output_file'),
                ])),
            ])),

            # htmx partials for new and existing works
            path('/work/form/', include([
                path('find-duplicate', works.FindPossibleDuplicatesView.as_view(), name='work_form_find_duplicates'),
                path('find-publication', works.FindPublicationDocumentView.as_view(), name='work_form_find_publication_document'),
                path('attach-publication', works.WorkFormPublicationDocumentView.as_view(), name='work_form_attach_publication_document'),
                path('localities', works.WorkFormLocalityView.as_view(), name='work_form_locality'),
                path('repeal', works.WorkFormRepealView.as_view(), name='work_form_repeal'),
                path('parent', works.WorkFormParentView.as_view(), name='work_form_parent'),
            ])),
        ]))
    ])),

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
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/$', amendments.WorkAmendmentsView.as_view(), name='work_amendments'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/new$', amendments.AddWorkAmendmentView.as_view(), name='new_work_amendment'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/arbitrary_expression_dates/new$', works.AddArbitraryExpressionDateView.as_view(), name='new_arbitrary_expression_date'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/arbitrary_expression_dates/(?P<arbitrary_expression_date_id>\d+)/edit$', works.EditArbitraryExpressionDateView.as_view(), name='edit_arbitrary_expression_date'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)$', amendments.WorkAmendmentUpdateView.as_view(), name='work_amendment_detail'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)/dropdown$', amendments.WorkAmendmentDropdownView.as_view(), name='work_amendment_dropdown'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)/instructions$', amendments.AmendmentInstructionsView.as_view(), name='work_amendment_instructions'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)/instructions/(?P<pk>\d+)$', amendments.AmendmentInstructionDetailView.as_view(), name='work_amendment_instruction_detail'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)/instructions/(?P<pk>\d+)/edit$', amendments.AmendmentInstructionEditView.as_view(), name='work_amendment_instruction_edit'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)/instructions/(?P<pk>\d+)/delete$', amendments.AmendmentInstructionDeleteView.as_view(), name='work_amendment_instruction_delete'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)/instructions/clear$', amendments.AmendmentInstructionClearView.as_view(), name='work_amendment_instruction_clear'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)/instructions/(?P<pk>\d+)/applied$', amendments.AmendmentInstructionStateChangeView.as_view(change='applied'), name='work_amendment_instruction_applied'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)/instructions/(?P<pk>\d+)/unapplied$', amendments.AmendmentInstructionStateChangeView.as_view(change='unapplied'), name='work_amendment_instruction_unapplied'),
    re_path(r'^works(?P<frbr_uri>/\S+?)/amendments/(?P<amendment_id>\d+)/instructions/new$', amendments.AmendmentInstructionCreateView.as_view(), name='work_amendment_instruction_new'),
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

    path('documents/<int:doc_id>/', include([
        path('', documents.DocumentDetailView.as_view(), name='document'),
        path('choose-provision', documents.ChooseDocumentProvisionView.as_view(), name='choose_document_provision'),
        path('popup', cache_page(POPUP_CACHE_SECS)(documents.DocumentPopupView.as_view()), name='document_popup'),
        path('provision/<str:eid>', documents.DocumentProvisionDetailView.as_view(), name='document_provision'),
        path('provision/<str:eid>/embed', documents.DocumentProvisionEmbedView.as_view(), name='document_provision_embed'),
    ])),

    path('tasks/', tasks.UserTasksView.as_view(), name='my_tasks'),
    path('tasks/all/', tasks.AllTasksView.as_view(), name='all_tasks'),

    path('comments/', include('django_comments.urls')),

]
