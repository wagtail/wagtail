from __future__ import absolute_import, unicode_literals

import json

from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.widgets import AdminChooser
from wagtail.wagtailembeds.models import Embed


class AdminEmbedChooser(AdminChooser):
    choose_one_text = _('Choose an embed')
    choose_another_text = _('Choose another embed')

    def __init__(self, **kwargs):
        super(AdminEmbedChooser, self).__init__(**kwargs)

    def render_html(self, name, value, attrs):
        instance, value = self.get_instance_and_id(Embed, value)
        original_field_html = super(AdminEmbedChooser, self).render_html(name, value, attrs)

        return render_to_string("wagtailembeds/widgets/embed_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'embed': instance,
        })

    def render_js_init(self, id_, name, value):
        return "createEmbedChooser({0});".format(json.dumps(id_))
