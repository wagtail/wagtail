from django.conf.urls import url

from wagtail.wagtailadmin.modules.models import ModelModule

from wagtail.wagtailimages.views import images, multiple, chooser


class ImageModelModule(ModelModule):
    index_view = images.ImageIndexView
    create_view = images.ImageCreateView
    update_view = images.ImageUpdateView
    delete_view = images.ImageDeleteView

    url_generator_view = images.ImageURLGeneratorView
    generate_url_view = images.ImageGenerateURLView
    preview_view = images.ImagePreviewView
    usage_view = images.ImageUsageView

    create_multiple_view = multiple.ImageCreateMultipleView
    create_multiple_update_view = multiple.ImageCreateMultipleUpdateView
    create_multiple_delete_view = multiple.ImageCreateMultipleDeleteView

    chooser_view = chooser.ImageChooserView
    chooser_chosen_view = chooser.ImageChooserChosenView
    chooser_upload_view = chooser.ImageChooserUploadView
    chooser_select_format_view = chooser.ImageChooserSelectFormatView

    def get_urls(self):
        urls = super(ImageModelModule, self).get_urls()
        urls += (
            url(r'^(?P<pk>\d+)/generate_url/$', self.url_generator_view.as_view(module=self), name='url_generator'),
            url(r'^(?P<pk>\d+)/generate_url/(?P<filter_spec>.*)/$', self.generate_url_view.as_view(module=self), name='generate_url'),
            url(r'^(?P<pk>\d+)/preview/(?P<filter_spec>.*)/$', self.preview_view.as_view(module=self), name='preview'),
            url(r'^(?P<pk>\d+)/usage/$', self.usage_view.as_view(module=self), name='image_usage'),
 
            url(r'^new/multiple/$',self.create_multiple_view.as_view(module=self), name='create_multiple'),
            url(r'^new/multiple/update/(?P<pk>\d+)/$', self.create_multiple_update_view.as_view(module=self), name='create_multiple_update'),
            url(r'^new/multiple/delete/(?P<pk>\d+)/$', self.create_multiple_delete_view.as_view(module=self), name='create_multiple_delete'),

            url(r'^chooser/$', self.chooser_view.as_view(module=self), name='chooser'),
            url(r'^chooser/(?P<pk>\d+)/$', self.chooser_chosen_view.as_view(module=self), name='chooser_chosen'),
            url(r'^chooser/upload/$', self.chooser_upload_view.as_view(module=self), name='chooser_upload'),
            url(r'^chooser/(?P<pk>\d+)/select_format/$', self.chooser_select_format_view.as_view(module=self), name='chooser_select_format'),
        )

        return urls
