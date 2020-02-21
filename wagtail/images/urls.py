from django.urls import path

from wagtail.images.views.serve import serve

urlpatterns = [
    path('<str:signature>/<int:image_id>/<str:filter_spec>/', serve, name="wagtailimages_serve"),
    path('<str:signature>/<int:image_id>/<str:filter_spec>/<str:filename>', serve, name="wagtailimages_serve")
]
