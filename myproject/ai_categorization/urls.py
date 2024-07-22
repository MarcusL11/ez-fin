from django.urls import path
from . import views

urlpatterns = []

htmx_urlpatterns = [
    path("ai_categorize/", views.ai_categorize, name="ai_categorize"),
]

urlpatterns += htmx_urlpatterns
