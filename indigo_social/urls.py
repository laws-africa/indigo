from django.conf.urls import url

from . import views

app_name = 'indigo_social'
urlpatterns = [
    # /social
    url(r'^$', views.SocialHomeView.as_view(), name='social_home'),
    # /social/{ user profile pk }
    url(r'^/(?P<pk>[0-9]+)', views.SocialProfileView.as_view(), name='social_profile'),
    # /social/my_profile/edit -- replace this too
    # once I can get the next one down to work (line 15)
    url(r'^/my_profile/edit$', views.SocialProfileEditView.as_view(), name='social_profile_edit'),
    # /social/{ user profile pk }/edit
    # url(r'^/(?P<pk>[0-9]+)/edit$', views.SocialProfileEditView.as_view(), name='social_profile_edit'),
]
