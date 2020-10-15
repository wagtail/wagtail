import json

from django import forms
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from wagtail.admin.staticfiles import versioned_static
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

        # Must import here because doing so at the top of the file is too early in the bootstrap.
        # from wagtail.images.permissions import permission_policy
        # if not permission_policy.user_has_permission_for_instance(user, 'change', instance):
        #     self.show_edit_link = False

        return render_to_string("wagtailimages/widgets/image_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'image': instance,
        })

    def render_js_init(self, id_, name, value):
        return "createImageChooser({0});".format(json.dumps(id_))

    @property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtailimages/js/image-chooser-modal.js'),
            versioned_static('wagtailimages/js/image-chooser.js'),
        ])
