from django.conf.urls import url

from wagtail.wagtailimages.views import images, multiple, chooser
from wagtail.wagtailadmin.modules.base import Module


class ImageModelModule(Module):
    app_name = 'wagtailimages'

    def get_urls(self):
        index_view = images.index
        create_view = images.add
        update_view = images.edit
        delete_view = images.delete
        url_generator_view = images.url_generator
        generate_url_view = images.generate_url
        preview_view = images.preview
        usage_view = images.usage

        create_multiple_view = multiple.add
        create_multiple_update_view = multiple.edit
        create_multiple_delete_view = multiple.delete

        chooser_view = chooser.chooser
        chooser_chosen_view = chooser.image_chosen
        chooser_upload_view = chooser.chooser_upload
        chooser_select_format_view = chooser.chooser_select_format

        return (
            url(r'^$', index_view, name='index'),
            url(r'^add/$', create_view, name='create'),
            url(r'^(\d+)/$', update_view, name='update'),
            url(r'^(\d+)/delete/$', delete_view, name='delete'),
            url(r'^(\d+)/generate_url/$', url_generator_view, name='url_generator'),
            url(r'^(\d+)/generate_url/(.*)/$', generate_url_view, name='generate_url'),
            url(r'^(\d+)/preview/(.*)/$', preview_view, name='preview'),
            url(r'^usage/(\d+)/$', usage_view, name='usage'),

            url(r'^multiple/add/$', create_multiple_view, name='create_multiple'),
            url(r'^multiple/(\d+)/$', create_multiple_update_view, name='create_multiple_update'),
            url(r'^multiple/(\d+)/delete/$', create_multiple_delete_view, name='create_multiple_delete'),

            url(r'^chooser/$', chooser_view, name='chooser'),
            url(r'^chooser/(\d+)/$', chooser_chosen_view, name='chooser_chosen'),
            url(r'^chooser/upload/$', chooser_upload_view, name='chooser_upload'),
            url(r'^chooser/(\d+)/select_format/$', chooser_select_format_view, name='chooser_select_format'),
        )
