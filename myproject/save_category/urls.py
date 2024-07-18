from django.urls import path
from . import views


urlpatterns = []

htmx_urlpatterns = [
    path("save_category/", views.save_category, name="save_category"),
    path("edit_category/", views.edit_category, name="edit_category"),
]

urlpatterns += htmx_urlpatterns
