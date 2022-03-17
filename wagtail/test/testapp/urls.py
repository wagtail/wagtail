from django.urls import path

from wagtail.test.testapp.views import bob_only_zone, message_test

urlpatterns = [
    path("bob-only-zone", bob_only_zone, name="testapp_bob_only_zone"),
    path("messages/", message_test, name="testapp_message_test"),
]
