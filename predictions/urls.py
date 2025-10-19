from django.urls import path, include
from .views import predict
from django.conf import settings
from django.conf.urls.static import static

app_name = "predictions"

urlpatterns = [
    path("predict/", predict, name="predict"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


