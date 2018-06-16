from django.conf.urls import url, include
from viewflow.flow.viewset import FlowViewSet

from .flows import ListWorksFlow


urlpatterns = [
    url(r'^listworks/', include(FlowViewSet(ListWorksFlow).urls), name='list-works'),
]
