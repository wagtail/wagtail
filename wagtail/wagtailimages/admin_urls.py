from django.conf.urls import url

from wagtail.wagtailimages.views import images, chooser, multiple


urlpatterns = [
    url(r'^$', images.ImageIndexView.as_view(), name='wagtailimages_index'),
    url(r'^(\d+)/$', images.ImageUpdateView.as_view(), name='wagtailimages_edit_image'),
    url(r'^(\d+)/delete/$', images.ImageDeleteView.as_view(), name='wagtailimages_delete_image'),
    url(r'^(\d+)/generate_url/$', images.ImageURLGeneratorView.as_view(), name='wagtailimages_url_generator'),
    url(r'^(\d+)/generate_url/(.*)/$', images.ImageGenerateURLView.as_view(), name='wagtailimages_generate_url'),
    url(r'^(\d+)/preview/(.*)/$', images.ImagePreviewView.as_view(), name='wagtailimages_preview'),
    url(r'^add/$', images.ImageCreateView.as_view(), name='wagtailimages_add_image'),
    url(r'^usage/(\d+)/$', images.ImageUsageView.as_view(), name='wagtailimages_image_usage'),

    url(r'^multiple/add/$', multiple.ImageCreateMultipleView.as_view(), name='wagtailimages_add_multiple'),
    url(r'^multiple/(\d+)/$', multiple.ImageCreateMultipleUpdateView.as_view(), name='wagtailimages_edit_multiple'),
    url(r'^multiple/(\d+)/delete/$', multiple.ImageCreateMultipleDeleteView.as_view(), name='wagtailimages_delete_multiple'),

    url(r'^chooser/$', chooser.ImageChooserView.as_view(), name='wagtailimages_chooser'),
    url(r'^chooser/(\d+)/$', chooser.ImageChooserChosenView.as_view(), name='wagtailimages_image_chosen'),
    url(r'^chooser/upload/$', chooser.ImageChooserUploadView.as_view(), name='wagtailimages_chooser_upload'),
    url(r'^chooser/(\d+)/select_format/$', chooser.ImageChooserSelectFormatView.as_view(), name='wagtailimages_chooser_select_format'),
]
