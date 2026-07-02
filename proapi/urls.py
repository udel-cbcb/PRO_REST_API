from django.conf.urls import url, include

urlpatterns = [
    url(r'^', include('api_v1.urls', namespace='api_v1')),
]
