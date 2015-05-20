from django.conf.urls import url

from wagtail.wagtailimages.views import images, chooser, multiple


urlpatterns = [
    url(r'^$', images.index, name='index'),
    url(r'^(\d+)/$', images.edit, name='edit_image'),
    url(r'^(\d+)/delete/$', images.delete, name='delete_image'),
    url(r'^(\d+)/generate_url/$', images.url_generator, name='url_generator'),
    url(r'^(\d+)/generate_url/(.*)/$', images.generate_url, name='generate_url'),
    url(r'^(\d+)/preview/(.*)/$', images.preview, name='preview'),
    url(r'^add/$', images.add, name='add_image'),
    url(r'^usage/(\d+)/$', images.usage, name='image_usage'),

    url(r'^multiple/add/$', multiple.add, name='add_multiple'),
    url(r'^multiple/(\d+)/$', multiple.edit, name='edit_multiple'),
    url(r'^multiple/(\d+)/delete/$', multiple.delete, name='delete_multiple'),

    url(r'^chooser/$', chooser.chooser, name='chooser'),
    url(r'^chooser/(\d+)/$', chooser.image_chosen, name='image_chosen'),
    url(r'^chooser/upload/$', chooser.chooser_upload, name='chooser_upload'),
    url(r'^chooser/(\d+)/select_format/$', chooser.chooser_select_format, name='chooser_select_format'),
]
