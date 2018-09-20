from django.conf.urls import url

from .views import ContributorsView, UserProfileView, UserProfileEditView

app_name = 'indigo_social'
urlpatterns = [
    # /contributors/
    url(r'^contributors/$', ContributorsView.as_view(), name='contributors'),
    # /contributors/{ user profile pk }
    url(r'^contributors/(?P<pk>[0-9]+)', UserProfileView.as_view(), name='user_profile'),
    # /accounts/profile/
    url(r'^accounts/profile/$', UserProfileEditView.as_view(), name='edit_account'),
]
