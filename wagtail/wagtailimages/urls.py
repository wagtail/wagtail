from django.conf.urls import url
from wagtail.wagtailimages.views import images, chooser

urlpatterns = [
    url(r'^$', images.index, name='wagtailimages_index'),
    url(r'^(\d+)/$', images.edit, name='wagtailimages_edit_image'),
    url(r'^(\d+)/delete/$', images.delete, name='wagtailimages_delete_image'),
    url(r'^add/$', images.add, name='wagtailimages_add_image'),

    url(r'^chooser/$', chooser.chooser, name='wagtailimages_chooser'),
    url(r'^chooser/(\d+)/$', chooser.image_chosen, name='wagtailimages_image_chosen'),
    url(r'^chooser/upload/$', chooser.chooser_upload, name='wagtailimages_chooser_upload'),
    url(r'^chooser/(\d+)/select_format/$', chooser.chooser_select_format, name='wagtailimages_chooser_select_format'),
]
