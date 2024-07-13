from django.urls import path
from . import views

urlpatterns = [
    path("upload_doc/", views.upload_doc, name="upload_doc"),
]
