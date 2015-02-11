from __future__ import absolute_import, unicode_literals

import json

from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin.widgets import AdminChooser


class AdminSnippetChooser(AdminChooser):
    target_content_type = None

    def __init__(self, content_type=None, **kwargs):
        if 'snippet_type_name' in kwargs:
            snippet_type_name = kwargs.pop('snippet_type_name')
            self.choose_one_text = _('Choose %s') % snippet_type_name
            self.choose_another_text = _('Choose another %s') % snippet_type_name

        super(AdminSnippetChooser, self).__init__(**kwargs)
        if content_type is not None:
            self.target_content_type = content_type

    def render_html(self, name, value, attrs):
        model_class = self.target_content_type.model_class()
        instance, value = self.get_instance_and_id(model_class, value)

        original_field_html = super(AdminSnippetChooser, self).render_html(name, value, attrs)

        return render_to_string("wagtailsnippets/widgets/snippet_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'item': instance,
        })

    def render_js_init(self, id_, name, value):
        content_type = self.target_content_type

        return "createSnippetChooser({id}, {content_type});".format(
            id=json.dumps(id_),
            content_type=json.dumps('{app}/{model}'.format(
                app=content_type.app_label,
                model=content_type.model)))
