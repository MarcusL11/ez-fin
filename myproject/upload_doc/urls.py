from django.urls import path
from . import views

urlpatterns = [
    path("", views.upload_doc, name="upload_doc"),
    path("my_docs/", views.my_docs, name="my_docs"),
    path(
        "my_docs/<int:pk>/<slug:transaction_type_slug>",
        views.my_docs_detail,
        name="my_docs_detail",
    ),
]
