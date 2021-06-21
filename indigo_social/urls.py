from django.urls import path, re_path
from django.views.decorators.cache import cache_page

import indigo_social.views as views

app_name = 'indigo_social'
urlpatterns = [
    # /contributors/
    path('contributors/', views.ContributorsView.as_view(), name='contributors'),
    # /contributors/{ username }
    re_path(r'^contributors/(?P<username>[\w@.-]+)$', views.UserProfileView.as_view(), name='user_profile'),
    re_path(r'^contributors/(?P<username>[\w@.-]+)/badges/award$', views.AwardBadgeView.as_view(), name='award_user_badge'),
    re_path(r'^contributors/(?P<username>[\w@.-]+)/badges/unaward$', views.UnawardBadgeView.as_view(), name='unaward_user_badge'),
    re_path(r'^contributors/(?P<username>[\w@.-]+)/activity/$', views.UserActivityView.as_view(), name='user_activity'),
    re_path(r'^contributors/(?P<username>[\w@.-]+)/tasks/$', views.UserTasksView.as_view(), name='user_tasks'),
    re_path(r'^contributors/(?P<username>[\w@.-]+)/popup$', views.UserPopupView.as_view(), name='user_popup'),
    re_path(r'^contributors/(?P<username>[\w@.-]+)/avatar/(?P<nonce>[\w@.-]+)$', cache_page(60 * 60 * 24 * 365)(views.UserProfilePhotoView.as_view()), name='user_profile_photo'),

    # /accounts/profile/
    path('accounts/profile/', views.UserProfileEditView.as_view(), name='edit_account'),

    path('badges/', views.BadgeListView.as_view(), name='badges'),
    re_path(r'^badges/(?P<slug>[\w-]+)/$', views.BadgeDetailView.as_view(), name='badge_detail'),
]
