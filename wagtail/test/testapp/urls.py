from django.urls import path

from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.test.testapp import views

api_router = WagtailAPIRouter("testapp_api_v2")
api_router.register_endpoint("test_issue_10411", views.Test10411ApiViewSet)

urlpatterns = [
    path("bob-only-zone", views.bob_only_zone, name="testapp_bob_only_zone"),
    path("messages/", views.message_test, name="testapp_message_test"),
    path("test-index/", views.TestIndexView.as_view(), name="testapp_generic_index"),
    path(
        "test-edit/<str:pk>/", views.TestEditView.as_view(), name="testapp_generic_edit"
    ),
    path(
        "test-delete/<str:pk>/",
        views.TestDeleteView.as_view(),
        name="testapp_generic_delete",
    ),
    path("api/v2/", api_router.urls),
]
