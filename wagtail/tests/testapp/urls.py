from django.conf.urls import url
from wagtail.tests.testapp.views import bob_only_zone

urlpatterns = [
    url(r'^bob-only-zone$', bob_only_zone, name='testapp_bob_only_zone'),
]
