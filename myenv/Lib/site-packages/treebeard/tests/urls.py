from django.contrib import admin
from django.urls import path

admin.autodiscover()

urlpatterns = [
    path("admin/", admin.site.urls),
]
