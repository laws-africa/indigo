from django.conf.urls import url

from .views import ContributorsView, UserProfileView, UserProfileEditView, BadgeListView, BadgeDetailView

app_name = 'indigo_social'
urlpatterns = [
    # /contributors/
    url(r'^contributors/$', ContributorsView.as_view(), name='contributors'),
    # /contributors/{ user profile pk }
    url(r'^contributors/(?P<pk>[0-9]+)', UserProfileView.as_view(), name='user_profile'),
    # /accounts/profile/
    url(r'^accounts/profile/$', UserProfileEditView.as_view(), name='edit_account'),

    url(r'^badges/$', BadgeListView.as_view(), name='badges'),
    url(r'^badges/(?P<slug>[\w-]+)/$', BadgeDetailView.as_view(), name='badge_detail'),
]
