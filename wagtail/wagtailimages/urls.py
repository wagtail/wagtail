from django.conf.urls import url

from wagtail.wagtailimages.views import frontend


urlpatterns = [
    url(r'^(.*)/(\d*)/(.*)/$', frontend.serve, name='wagtailimages_serve'),
]
