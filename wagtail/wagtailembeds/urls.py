from django.conf.urls import url
from wagtail.wagtailembeds.views import chooser


urlpatterns = [
    url(r'^chooser/$', chooser.chooser, name='chooser'),
    url(r'^chooser/upload/$', chooser.chooser_upload, name='chooser_upload'),
]
