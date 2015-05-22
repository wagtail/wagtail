from __future__ import absolute_import, unicode_literals

import json

from django.db import models
from django import forms
from django.core.serializers.json import DjangoJSONEncoder
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


class LazyField(object):
    """
    An object descriptor that lazily prepares the contents of a field by
    calling `field.to_python` when the field is first accessed. This helps
    reduce unnecessary load when fields are costly to prepare, but not always
    used.
    """
    # Adapted from `django-json-field`s `json_field.fields.Creator`, itself
    # adapted from `django`s `django.db.models.fields.subclassing.Creator`.

    _state_key = '_streamfield_state'

    def __init__(self, field):
        self.field = field

    def __get__(self, obj, type=None):
        if obj is None:
            return self

        state = getattr(obj, self._state_key, None)
        if state is None:
            state = {}
            setattr(obj, self._state_key, state)

        if state.get(self.field.name, False):
            return obj.__dict__[self.field.name]

        value = self.field.to_python(obj.__dict__[self.field.name])
        obj.__dict__[self.field.name] = value
        state[self.field.name] = True

        return value

    def __set__(self, obj, value):
        obj.__dict__[self.field.name] = value


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

    def get_panel(self):
        from wagtail.wagtailadmin.edit_handlers import StreamFieldPanel
        return StreamFieldPanel

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
            try:
                unpacked_value = json.loads(value)
            except ValueError:
                # value is not valid JSON; most likely, this field was previously a
                # rich text field before being migrated to StreamField, and the data
                # was left intact in the migration. Return an empty stream instead.

                # TODO: keep this raw text data around as a property of the StreamValue
                # so that it can be retrieved in data migrations
                return StreamValue(self.stream_block, [])

            if unpacked_value is None:
                # we get here if value is the literal string 'null'. This should probably
                # never happen if the rest of the (de)serialization code is working properly,
                # but better to handle it just in case...
                return StreamValue(self.stream_block, [])

            return self.stream_block.to_python(unpacked_value)

    def get_prep_value(self, value):
        return json.dumps(self.stream_block.get_prep_value(value), cls=DjangoJSONEncoder)

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


# SubfieldBase does some trickery that overrides `contribute_to_class`.
# We need to subvert that process, and handle it ourselves to get the lazy
# functionality working. This requires working around the metaclass, hence why
# this is done outside the class decleration.
def contribute_to_class(self, cls, name):
    super(StreamField, self).contribute_to_class(cls, name)
    # Use `LazyField` to parse `StreamField` content only as it is needed.
    # This stops the `StreamField` from doing database lookups and other
    # expensive operations when the parent model is loaded, but the
    # `StreamField` is not accessed.
    setattr(cls, name, LazyField(self))
StreamField.contribute_to_class = contribute_to_class
