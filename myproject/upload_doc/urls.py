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

htmx_urlpatterns = [
    path("pagination_view/", views.pagination_view, name="pagination_view"),
    path("delete_doc/", views.delete_doc, name="delete_doc"),
    path(
        "my_docs_pagination_view/",
        views.my_docs_pagination_view,
        name="my_docs_pagination_view",
    ),
]

urlpatterns += htmx_urlpatterns
