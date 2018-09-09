from django.conf.urls import url
from django.views.generic.base import RedirectView

from .views import profile

urlpatterns = [
    # in theory: /social/
    url(r'^$', RedirectView.as_view(url='profile', permanent=True)),
    url(r'^profile/$', profile.ProfileView.as_view()),
]
