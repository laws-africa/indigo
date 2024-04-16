from django.urls import include, re_path


app_name = 'indigo_content_api'

# Versioned API URLs are now enforced (from v3)
urlpatterns = [
    re_path(r'(?P<version>v2)/', include('indigo_content_api.v2.urls')),
    re_path(r'(?P<version>v3)/', include('indigo_content_api.v3.urls')),
]
