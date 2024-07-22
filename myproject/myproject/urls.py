from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("upload_doc/", include("upload_doc.urls")),
    path("save_category/", include("save_category.urls")),
    path("ai_categorization/", include("ai_categorization.urls")),
    path("category/", include("category.urls")),
    path("", include("landing.urls")),
    path("", include("download_csv.urls")),
]

# if not settings.TESTING:
#     urlpatterns = [
#         *urlpatterns,
#         path("__debug__/", include("debug_toolbar.urls")),
#     ]
