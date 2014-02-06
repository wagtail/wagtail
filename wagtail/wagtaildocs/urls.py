from django.conf.urls import patterns, url

urlpatterns = patterns(
    'wagtail.wagtaildocs.views',
    url(r'^(\d+)/(.*)$', 'serve.serve', name='wagtaildocs_serve'),
)
