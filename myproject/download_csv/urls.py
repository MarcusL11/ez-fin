from django.urls import path
from . import views


urlpatterns = [
    path("download-csv/<int:document_id>/", views.download_csv, name="download_csv"),
]


htmx_urlpatterns = []

urlpatterns += htmx_urlpatterns
