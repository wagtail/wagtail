from django.conf.urls import url

from wagtail.images.views.serve import serve

urlpatterns = [
    url(r'^([^/]*)/(\d*)/([^/]*)/[^/]*$', serve, name='wagtailimages_serve'),
]
