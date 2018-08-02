import json

from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.widgets import AdminChooser
from wagtail.images import get_image_model


class AdminImageChooser(AdminChooser):
    choose_one_text = _('Choose an image')
    choose_another_text = _('Change image')
    link_to_chosen_text = _('Edit this image')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_model = get_image_model()

    def render_html(self, name, value, attrs):
        instance, value = self.get_instance_and_id(self.image_model, value)
        original_field_html = super().render_html(name, value, attrs)

        return render_to_string("wagtailimages/widgets/image_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'image': instance,
        })

    def render_js_init(self, id_, name, value):
        return "createImageChooser({0});".format(json.dumps(id_))

    class Media:
        js = [
            'wagtailimages/js/image-chooser-modal.js',
            'wagtailimages/js/image-chooser.js',
        ]

#HT START
class SelectCropAdminImageChooser(AdminImageChooser):

    def render_html(self, name, value, attrs):
        #it is important to remember the difference between the json focal_point values of the parent (contextual) and the focal point values accessible as image properties
        #which belong to the image..  the json contextual values cannot be obtained in here
        max_dim = getattr(settings, 'PREVIEW_IMAGE_SIZE', 165)
        instance, value = self.get_instance_and_id(self.image_model, value)
        original_field_html = super(AdminImageChooser, self).render_html(name, value, attrs)#skips the AdminImageChooser and calls its parent's method to avoid double call

        print('value: {}'.format(value))
        print('attrs: {}'.format(attrs))
        print('image: {}'.format(instance))
        print('self: {}'.format(self.__dict__))
        print('original_field_html: {}'.format(original_field_html))

        return render_to_string("wagtailimages/widgets/select_crop_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'image': instance,
            'admin_preview_rendition': instance.get_rendition('max-{}x{}'.format(max_dim,max_dim)) if instance else None
        })
#HT END