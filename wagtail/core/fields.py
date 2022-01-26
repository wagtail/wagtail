import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.encoding import force_str

from wagtail.core.blocks import Block, BlockField, StreamBlock, StreamValue
from wagtail.core.rich_text import get_text_for_indexing


class RichTextField(models.TextField):
    def __init__(self, *args, **kwargs):
        # 'editor' and 'features' are popped before super().__init__ has chance to capture them
        # for use in deconstruct(). This is intentional - they would not be useful in migrations
        # and retrospectively adding them would generate unwanted migration noise
        self.editor = kwargs.pop('editor', 'default')
        self.features = kwargs.pop('features', None)
        super().__init__(*args, **kwargs)

    def clone(self):
        name, path, args, kwargs = self.deconstruct()
        # add back the 'features' and 'editor' kwargs that were not preserved by deconstruct()
        kwargs["features"] = self.features
        kwargs["editor"] = self.editor
        return self.__class__(*args, **kwargs)

    def formfield(self, **kwargs):
        from wagtail.admin.rich_text import get_rich_text_editor_widget
        defaults = {'widget': get_rich_text_editor_widget(self.editor, features=self.features)}
        defaults.update(kwargs)
        return super().formfield(**defaults)

    def get_searchable_content(self, value):
        # Strip HTML tags to prevent search backend from indexing them
        source = force_str(value)
        return [get_text_for_indexing(source)]


# https://github.com/django/django/blob/64200c14e0072ba0ffef86da46b2ea82fd1e019a/django/db/models/fields/subclassing.py#L31-L44
class Creator:
    """
    A placeholder class that provides a way to set the attribute on the model.
    """
    def __init__(self, field):
        self.field = field

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        field_name = self.field.name

        if field_name not in obj.__dict__:
            # Field is deferred. Fetch it from db.
            obj.refresh_from_db(fields=[field_name])
        return obj.__dict__[field_name]

    def __set__(self, obj, value):
        obj.__dict__[self.field.name] = self.field.to_python(value)


class StreamField(models.Field):
    def __init__(self, block_types, **kwargs):

        # extract kwargs that are to be passed on to the block, not handled by super
        block_opts = {}
        for arg in ['min_num', 'max_num', 'block_counts', 'collapsed']:
            if arg in kwargs:
                block_opts[arg] = kwargs.pop(arg)

        # for a top-level block, the 'blank' kwarg (defaulting to False) always overrides the
        # block's own 'required' meta attribute, even if not passed explicitly; this ensures
        # that the field and block have consistent definitions
        block_opts['required'] = not kwargs.get('blank', False)

        super().__init__(**kwargs)

        if isinstance(block_types, Block):
            # use the passed block as the top-level block
            self.stream_block = block_types
        elif isinstance(block_types, type):
            # block passed as a class - instantiate it
            self.stream_block = block_types()
        else:
            # construct a top-level StreamBlock from the list of block types
            self.stream_block = StreamBlock(block_types)

        self.stream_block.set_meta_options(block_opts)

    def get_internal_type(self):
        return 'TextField'

    def get_panel(self):
        from wagtail.admin.edit_handlers import StreamFieldPanel
        return StreamFieldPanel

    def deconstruct(self):
        name, path, _, kwargs = super().deconstruct()
        block_types = list(self.stream_block.child_blocks.items())
        args = [block_types]
        return name, path, args, kwargs

    def to_python(self, value):
        if value is None or value == '':
            return StreamValue(self.stream_block, [])
        elif isinstance(value, StreamValue):
            return value
        elif isinstance(value, str):
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

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def formfield(self, **kwargs):
        """
        Override formfield to use a plain forms.Field so that we do no transformation on the value
        (as distinct from the usual fallback of forms.CharField, which transforms it into a string).
        """
        defaults = {'form_class': BlockField, 'block': self.stream_block}
        defaults.update(kwargs)
        return super().formfield(**defaults)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)

    def get_searchable_content(self, value):
        return self.stream_block.get_searchable_content(value)

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(self.stream_block.check(field=self, **kwargs))
        return errors

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)

        # Add Creator descriptor to allow the field to be set from a list or a
        # JSON string.
        setattr(cls, self.name, Creator(self))
