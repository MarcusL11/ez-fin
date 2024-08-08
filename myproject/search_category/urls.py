from django.urls import path
from . import views

urlpatterns = []

htmx_urlpatterns = [
    path("search_category/", views.search_category, name="search_category"),
    path("active_search/", views.active_search, name="active_search"),
]

urlpatterns = urlpatterns + htmx_urlpatterns
