from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path

from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls

urlpatterns = [
    path("admin/", include(wagtailadmin_urls)),
]

urlpatterns += i18n_patterns(path("site/", include(wagtail_urls)))
