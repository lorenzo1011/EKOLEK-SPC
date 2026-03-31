"""URL configuration for the EKO project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Mobile API URLs must come BEFORE accounts URLs to avoid routing conflicts
    # Mobile uses JWT auth, web uses session/CSRF
    path('', include('mobilelogin.urls')),  # Mobile API endpoints with JWT
    path('', include('accounts.urls')),     # Web dashboard with session auth
    path('', include('cenro.urls', namespace='cenro')),
    path('', include('game.urls')),
    path('', include('learn.urls')),
    path('mobile/', include('ekoscan.urls')),  # Mobile API endpoints
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)