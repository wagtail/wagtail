from __future__ import absolute_import, unicode_literals

import json
import django

from django.db import models
from django.forms import Textarea

if django.VERSION < (1, 7):
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^wagtail\.wagtailcore\.fields\.RichTextField"])

from wagtail.wagtailcore.rich_text import DbWhitelister, expand_db_html
from wagtail.utils.widgets import WidgetWithScript


class RichTextArea(WidgetWithScript, Textarea):
    def get_panel(self):
        from wagtail.wagtailadmin.edit_handlers import RichTextFieldPanel
        return RichTextFieldPanel

    def render(self, name, value, attrs=None):
        if value is None:
            translated_value = None
        else:
            translated_value = expand_db_html(value, for_editor=True)
        return super(RichTextArea, self).render(name, translated_value, attrs)

    def render_js_init(self, id_, name, value):
        return "makeRichTextEditable({0});".format(json.dumps(id_))

    def value_from_datadict(self, data, files, name):
        original_value = super(RichTextArea, self).value_from_datadict(data, files, name)
        if original_value is None:
            return None
        return DbWhitelister.clean(original_value)


class RichTextField(models.TextField):
    def formfield(self, **kwargs):
        defaults = {'widget': RichTextArea}
        defaults.update(kwargs)
        return super(RichTextField, self).formfield(**defaults)
