from django.urls import path
from . import views

urlpatterns = []

htmx_urlpatterns = [
    path("search_category/", views.search_category, name="search_category"),
]

urlpatterns = urlpatterns + htmx_urlpatterns
