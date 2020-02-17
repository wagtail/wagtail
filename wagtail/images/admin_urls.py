from django.urls import path, re_path

from wagtail.images.views import chooser, images, multiple

app_name = 'wagtailimages'
urlpatterns = [
    path('', images.index, name='index'),
    re_path(r'^(\d+)/$', images.edit, name='edit'),
    re_path(r'^(\d+)/delete/$', images.delete, name='delete'),
    re_path(r'^(\d+)/generate_url/$', images.url_generator, name='url_generator'),
    re_path(r'^(\d+)/generate_url/(.*)/$', images.generate_url, name='generate_url'),
    re_path(r'^(\d+)/preview/(.*)/$', images.preview, name='preview'),
    path('add/', images.add, name='add'),
    re_path(r'^usage/(\d+)/$', images.usage, name='image_usage'),

    path('multiple/add/', multiple.add, name='add_multiple'),
    re_path(r'^multiple/(\d+)/$', multiple.edit, name='edit_multiple'),
    re_path(r'^multiple/create_from_uploaded_image/(\d+)/$', multiple.create_from_uploaded_image, name='create_multiple_from_uploaded_image'),
    re_path(r'^multiple/(\d+)/delete/$', multiple.delete, name='delete_multiple'),
    re_path(r'^multiple/delete_upload/(\d+)/$', multiple.delete_upload, name='delete_upload_multiple'),

    path('chooser/', chooser.chooser, name='chooser'),
    re_path(r'^chooser/(\d+)/$', chooser.image_chosen, name='image_chosen'),
    path('chooser/upload/', chooser.chooser_upload, name='chooser_upload'),
    re_path(r'^chooser/(\d+)/select_format/$', chooser.chooser_select_format, name='chooser_select_format'),
]
