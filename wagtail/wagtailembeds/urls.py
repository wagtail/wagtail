from django.conf.urls import patterns, url


urlpatterns = patterns('wagtail.wagtailembeds.views',
    url(r'^chooser/$', 'chooser.chooser', name='wagtailembeds_chooser'),
    url(r'^chooser/upload/$', 'chooser.chooser_upload', name='wagtailembeds_chooser_upload'),
)
