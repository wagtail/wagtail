from django.urls import path, re_path

from wagtail.images.views import chooser, images, multiple

app_name = 'wagtailimages'
urlpatterns = [
    path('', images.index, name='index'),
    path('<int:image_id>/', images.edit, name='edit'),
    path('<int:image_id>/delete/', images.delete, name='delete'),
    path('<int:image_id>/generate_url/', images.url_generator, name='url_generator'),
    path('<int:image_id>/generate_url/<str:filter_spec>/', images.generate_url, name='generate_url'),
    path('<int:image_id>/preview/<str:filter_spec>/', images.preview, name='preview'),
    path('add/', images.add, name='add'),
    re_path(r'^usage/(\d+)/$', images.usage, name='image_usage'),

    path('multiple/add/', multiple.add, name='add_multiple'),
    re_path(r'^multiple/(\d+)/$', multiple.edit, name='edit_multiple'),
    re_path(r'^multiple/(\d+)/delete/$', multiple.delete, name='delete_multiple'),

    path('chooser/', chooser.chooser, name='chooser'),
    re_path(r'^chooser/(\d+)/$', chooser.image_chosen, name='image_chosen'),
    path('chooser/upload/', chooser.chooser_upload, name='chooser_upload'),
    re_path(r'^chooser/(\d+)/select_format/$', chooser.chooser_select_format, name='chooser_select_format'),
]
