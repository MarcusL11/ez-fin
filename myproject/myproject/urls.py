from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("upload_doc/", include("upload_doc.urls")),
]

# if not settings.TESTING:
#     urlpatterns = [
#         *urlpatterns,
#         path("__debug__/", include("debug_toolbar.urls")),
#     ]
