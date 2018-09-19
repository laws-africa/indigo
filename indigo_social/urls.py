from django.conf.urls import url

from . import views

app_name = 'indigo_social'
urlpatterns = [
    # /social
    url(r'^$', views.SocialHomeView.as_view(), name='social_home'),
    # /social/{ user profile pk }
    url(r'^/(?P<pk>[0-9]+)', views.SocialProfileView.as_view(), name='social_profile'),
    # /social/my_profile/edit
    url(r'^/my_profile/edit$', views.UserProfileEditView.as_view(), name='social_profile_edit'),
]
