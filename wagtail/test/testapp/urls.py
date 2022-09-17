from django.urls import path

from wagtail.test.testapp import views

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
]
