from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core.views import HomeView

urlpatterns = [
    path("admin/", admin.site.urls), #Base_url/admin/
    path("", HomeView.as_view(), name="home"),
    path("accounts/", include("accounts.urls")),
    path("families/", include("families.urls")),
    path("ledger/", include("ledger.urls")),
    path("assets/", include("assets.urls")),
    path("dashboard/", include("dashboard.urls")), #Base_url/dashboard/
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
