from django.conf.urls import url

from . import views

app_name = 'indigo_social'
urlpatterns = [
    # /social/
    url(r'^$', views.ISocialHome.as_view(), name='isoc_home'),
    # /social/my_profile
    url(r'^my_profile$', views.ISocialProfile.as_view(), name='isoc_profile'),
]
