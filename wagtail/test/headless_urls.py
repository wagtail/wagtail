"""An alternative urlconf module where Wagtail does not serve front-end URLs"""

from django.urls import include, path

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.images import urls as wagtailimages_urls

urlpatterns = [
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("images/", include(wagtailimages_urls)),
]
