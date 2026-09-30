from django.urls import path

from .v3.api import api

urlpatterns = [
    path("", api.urls),
]
