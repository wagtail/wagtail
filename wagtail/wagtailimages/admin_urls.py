from django.conf.urls import include, url

from wagtail.wagtailimages.modules import ImageModelModule

urlpatterns = [
    url(r'images/', include(ImageModelModule('wagtailimages').urls)),
]
