import json

from django import forms
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets import AdminChooser
from wagtail.images import get_image_model
from wagtail.images.shortcuts import get_rendition_or_not_found


class AdminImageChooser(AdminChooser):
    choose_one_text = _('Choose an image')
    choose_another_text = _('Change image')
    link_to_chosen_text = _('Edit this image')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_model = get_image_model()

    def render_html(self, name, value, attrs):
        image, value = self.get_instance_and_id(self.image_model, value)
        original_field_html = super().render_html(name, value, attrs)

        if image:
            preview_image = get_rendition_or_not_found(image, 'max-165x165')
        else:
            preview_image = None

        return render_to_string("wagtailimages/widgets/image_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'title': image.title if image else '',
            'preview': {
                'url': preview_image.url,
                'width': preview_image.width,
                'height': preview_image.height,
            } if preview_image else {},
            'edit_url': reverse('wagtailimages:edit', args=[image.id]) if image else '',
        })

    def render_js_init(self, id_, name, value):
        return "createImageChooser({0});".format(json.dumps(id_))

    @property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtailimages/js/image-chooser-modal.js'),
            versioned_static('wagtailimages/js/image-chooser.js'),
        ])
