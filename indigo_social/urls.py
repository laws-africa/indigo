from django.conf.urls import url

from .views import SocialHomeView, SocialProfileView, UserProfileEditView

app_name = 'indigo_social'
urlpatterns = [
    # /social
    url(r'^$', SocialHomeView.as_view(), name='social_home'),
    # /social/{ user profile pk }
    url(r'^/(?P<pk>[0-9]+)', SocialProfileView.as_view(), name='social_profile'),
    # /social/my_profile/edit
    url(r'^accounts/profile/$', UserProfileEditView.as_view(), name='edit_account'),
]
