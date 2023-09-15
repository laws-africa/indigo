from django.urls import include, path


APP_NAME = 'indigo_content_api'

# Versioned API URLs are now enforced (from v3)
urlpatterns = [
    path('v2/', include(('indigo_content_api.v2.urls', APP_NAME), namespace='v2')),
    path('v3/', include(('indigo_content_api.v3.urls', APP_NAME), namespace='v3')),
]
