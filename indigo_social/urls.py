from django.conf.urls import url

import indigo_social.views as views

app_name = 'indigo_social'
urlpatterns = [
    # /contributors/
    url(r'^contributors/$', views.ContributorsView.as_view(), name='contributors'),
    # /contributors/{ username }
    url(r'^contributors/(?P<username>[\w@.-]+)$', views.UserProfileView.as_view(), name='user_profile'),
    url(r'^contributors/(?P<username>[\w@.-]+)/badges$', views.AwardBadgeView.as_view(), name='award_user_badge'),

    # /accounts/profile/
    url(r'^accounts/profile/$', views.UserProfileEditView.as_view(), name='edit_account'),

    url(r'^badges/$', views.BadgeListView.as_view(), name='badges'),
    url(r'^badges/(?P<slug>[\w-]+)/$', views.BadgeDetailView.as_view(), name='badge_detail'),
]
