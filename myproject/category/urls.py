from django.urls import path
from . import views

urlpatterns = [
    path("category/", views.category, name="category"),
]

htmx_urlpatterns = []

urlpatterns = urlpatterns + htmx_urlpatterns
