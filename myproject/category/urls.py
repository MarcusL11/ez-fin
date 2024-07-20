from django.urls import path
from . import views

urlpatterns = [
    path("category/", views.category_list, name="category_list"),
]

htmx_urlpatterns = [
    path("add_category/", views.add_category_list, name="add_category_list"),
    path("edit_category/", views.edit_category_list, name="edit_category_list"),
    path("save_category/", views.save_category_list, name="save_category_list"),
]

urlpatterns = urlpatterns + htmx_urlpatterns
