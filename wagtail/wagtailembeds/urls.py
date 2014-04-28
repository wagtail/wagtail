from django.conf.urls import url
from wagtail.wagtailembeds.views import chooser


urlpatterns = [
    url(r'^chooser/$', chooser.chooser, name='wagtailembeds_chooser'),
    url(r'^chooser/upload/$', chooser.chooser_upload, name='wagtailembeds_chooser_upload'),
]
