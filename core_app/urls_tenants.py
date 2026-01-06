from django.contrib import admin
from django.urls import path, include
from themes import views as themes_views
from dashboard import views as dashboard_views

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # path("", themes_views.index, name="themes_home"),
    path("admin/", admin.site.urls),
    path("catalog/", include("catalog.urls")),
    path("", include("themes.urls")),
    path("", include("dashboard.urls")),
]

# ✅ Serve media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
