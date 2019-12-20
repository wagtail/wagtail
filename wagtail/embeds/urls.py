from django.conf.urls import url

from wagtail.embeds.views import chooser

app_name = 'wagtailembeds'
urlpatterns = [
    url(r'^chooser/$', chooser.chooser, name='chooser'),
    url(r'^chooser/upload/$', chooser.chooser_upload, name='chooser_upload'),
]
