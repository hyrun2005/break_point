from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("players.urls")),
    path("account/", include("accounts.urls")),
    path("predictions/", include("predictions.urls"))
]
