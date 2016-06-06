from __future__ import absolute_import, unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.six import string_types, with_metaclass

from wagtail.wagtailcore.blocks import Block, BlockField, StreamBlock, StreamValue


class RichTextField(models.TextField):
    def __init__(self, *args, **kwargs):
        self.editor = kwargs.pop('editor', 'default')
        super(RichTextField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        from wagtail.wagtailadmin.rich_text import get_rich_text_editor_widget
        defaults = {'widget': get_rich_text_editor_widget(self.editor)}
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
        elif isinstance(value, string_types):
            try:
                unpacked_value = json.loads(value)
            except ValueError:
                # value is not valid JSON; most likely, this field was previously a
                # rich text field before being migrated to StreamField, and the data
                # was left intact in the migration. Return an empty stream instead
                # (but keep the raw text available as an attribute, so that it can be
                # used to migrate that data to StreamField)
                return StreamValue(self.stream_block, [], raw_text=value)

            if unpacked_value is None:
                # we get here if value is the literal string 'null'. This should probably
                # never happen if the rest of the (de)serialization code is working properly,
                # but better to handle it just in case...
                return StreamValue(self.stream_block, [])

            return self.stream_block.to_python(unpacked_value)
        else:
            # See if it looks like the standard non-smart representation of a
            # StreamField value: a list of (block_name, value) tuples
            try:
                [None for (x, y) in value]
            except (TypeError, ValueError):
                # Give up trying to make sense of the value
                raise TypeError("Cannot handle %r (type %r) as a value of StreamField" % (value, type(value)))

            # Test succeeded, so return as a StreamValue-ified version of that value
            return StreamValue(self.stream_block, value)

    def get_prep_value(self, value):
        if isinstance(value, StreamValue) and not(value) and value.raw_text is not None:
            # An empty StreamValue with a nonempty raw_text attribute should have that
            # raw_text attribute written back to the db. (This is probably only useful
            # for reverse migrations that convert StreamField data back into plain text
            # fields.)
            return value.raw_text
        else:
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
        value = self.value_from_object(obj)
        return self.get_prep_value(value)

    def get_searchable_content(self, value):
        return self.stream_block.get_searchable_content(value)

    def check(self, **kwargs):
        errors = super(StreamField, self).check(**kwargs)
        errors.extend(self.stream_block.check(field=self, **kwargs))
        return errors
