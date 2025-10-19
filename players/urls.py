from django.urls import path, include
from players.views import home_page, atp_ranking
from django.conf.urls.static import static
from django.conf import settings

app_name = "players"

urlpatterns = [
    path("", home_page, name="home"),
    path("atp_ranking/", atp_ranking, name="atp_rating")
]

if settings.DEBUG:  # only in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
