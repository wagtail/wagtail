from __future__ import absolute_import, unicode_literals

import json

from django.db import models
from django import forms
from django.utils.six import with_metaclass

from wagtail.wagtailcore.rich_text import DbWhitelister, expand_db_html
from wagtail.utils.widgets import WidgetWithScript
from wagtail.wagtailcore.blocks import Block, StreamBlock, StreamValue, BlockField


class RichTextArea(WidgetWithScript, forms.Textarea):
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


class StreamField(with_metaclass(models.SubfieldBase, models.Field)):
    def __init__(self, block_types, **kwargs):
        if isinstance(block_types, Block):
            self.stream_block = block_types
        elif isinstance(block_types, type):
            self.stream_block = block_types()
        else:
            self.stream_block = StreamBlock(block_types)
        super(StreamField, self).__init__(**kwargs)

    def get_internal_type(self):
        return 'TextField'

    def deconstruct(self):
        name, path, _, kwargs = super(StreamField, self).deconstruct()
        block_types = self.stream_block.child_blocks.items()
        args = [block_types]
        return name, path, args, kwargs

    def to_python(self, value):
        if value is None or value == '':
            return StreamValue(self.stream_block, [])
        elif isinstance(value, StreamValue):
            return value
        else:  # assume string
            return self.stream_block.to_python(json.loads(value))

    def get_prep_value(self, value):
        return json.dumps(self.stream_block.get_prep_value(value))

    def formfield(self, **kwargs):
        """
        Override formfield to use a plain forms.Field so that we do no transformation on the value
        (as distinct from the usual fallback of forms.CharField, which transforms it into a string).
        """
        defaults = {'form_class': BlockField, 'block': self.stream_block}
        defaults.update(kwargs)
        return super(StreamField, self).formfield(**defaults)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)

    def get_searchable_content(self, value):
        return self.stream_block.get_searchable_content(value)
