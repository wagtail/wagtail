from django.urls import re_path

from wagtail.images.views.serve import serve

urlpatterns = [
    re_path(r"^([^/]*)/(\d*)/([^/]*)/[^/]*$", serve, name="wagtailimages_serve"),
]
