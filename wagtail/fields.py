import json

from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MaxLengthValidator
from django.db import models
from django.db.models.fields.json import KeyTransform
from django.utils.encoding import force_str
from django.utils.functional import cached_property

from wagtail.blocks import Block, BlockField, StreamBlock, StreamValue
from wagtail.blocks.definition_lookup import (
    BlockDefinitionLookup,
    BlockDefinitionLookupBuilder,
)
from wagtail.rich_text import (
    RichTextMaxLengthValidator,
    extract_references_from_rich_text,
    get_text_for_indexing,
)


class RichTextField(models.TextField):
    def __init__(self, *args, **kwargs):
        # 'editor' and 'features' are popped before super().__init__ has chance to capture them
        # for use in deconstruct(). This is intentional - they would not be useful in migrations
        # and retrospectively adding them would generate unwanted migration noise
        self.editor = kwargs.pop("editor", "default")
        self.features = kwargs.pop("features", None)

        super().__init__(*args, **kwargs)

    def clone(self):
        name, path, args, kwargs = self.deconstruct()
        # add back the 'features' and 'editor' kwargs that were not preserved by deconstruct()
        kwargs["features"] = self.features
        kwargs["editor"] = self.editor
        return self.__class__(*args, **kwargs)

    def formfield(self, **kwargs):
        from wagtail.admin.rich_text import get_rich_text_editor_widget

        defaults = {
            "widget": get_rich_text_editor_widget(self.editor, features=self.features)
        }
        defaults.update(kwargs)
        field = super().formfield(**defaults)

        # replace any MaxLengthValidators with RichTextMaxLengthValidators to ignore tags
        for i, validator in enumerate(field.validators):
            if isinstance(validator, MaxLengthValidator):
                field.validators[i] = RichTextMaxLengthValidator(
                    validator.limit_value, message=validator.message
                )

        return field

    def get_searchable_content(self, value):
        # Strip HTML tags to prevent search backend from indexing them
        source = force_str(value)
        return [get_text_for_indexing(source)]

    def extract_references(self, value):
        yield from extract_references_from_rich_text(force_str(value))


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
    def __init__(self, block_types, use_json_field=True, block_lookup=None, **kwargs):
        """
        Construct a StreamField.

        :param block_types: Either a list of block types that are allowed in this StreamField
            (as a list of tuples of block name and block instance) or a StreamBlock to use as
            the top level block (as a block instance or class).
        :param use_json_field: Ignored, but retained for compatibility with historical migrations.
        :param block_lookup: Used in migrations to provide a more compact block definition -
            see ``wagtail.blocks.definition_lookup.BlockDefinitionLookup``. If passed, ``block_types``
            can contain integer indexes into this lookup table, in place of actual block instances.
        """

        # extract kwargs that are to be passed on to the block, not handled by super
        self.block_opts = {}
        for arg in ["min_num", "max_num", "block_counts", "collapsed"]:
            if arg in kwargs:
                self.block_opts[arg] = kwargs.pop(arg)

        # for a top-level block, the 'blank' kwarg (defaulting to False) always overrides the
        # block's own 'required' meta attribute, even if not passed explicitly; this ensures
        # that the field and block have consistent definitions
        self.block_opts["required"] = not kwargs.get("blank", False)

        # Store the `block_types` and `block_lookup` arguments to be handled in the `stream_block`
        # property
        self.block_types_arg = block_types
        self.block_lookup = block_lookup

        super().__init__(**kwargs)

    @cached_property
    def stream_block(self):
        has_block_lookup = self.block_lookup is not None
        if has_block_lookup:
            lookup = BlockDefinitionLookup(self.block_lookup)

        if isinstance(self.block_types_arg, Block):
            # use the passed block as the top-level block
            block = self.block_types_arg
        elif isinstance(self.block_types_arg, int) and has_block_lookup:
            # retrieve block from lookup table to use as the top-level block
            block = lookup.get_block(self.block_types_arg)
        elif isinstance(self.block_types_arg, type):
            # block passed as a class - instantiate it
            block = self.block_types_arg()
        else:
            # construct a top-level StreamBlock from the list of block types.
            # If an integer is found in place of a block instance, and block_lookup is
            # provided, it will be replaced with the corresponding block definition.
            child_blocks = []

            for name, child_block in self.block_types_arg:
                if isinstance(child_block, int) and has_block_lookup:
                    child_blocks.append((name, lookup.get_block(child_block)))
                else:
                    child_blocks.append((name, child_block))

            block = StreamBlock(child_blocks)

        block.set_meta_options(self.block_opts)
        return block

    @property
    def json_field(self):
        return models.JSONField(encoder=DjangoJSONEncoder)

    def get_internal_type(self):
        return "JSONField"

    def get_lookup(self, lookup_name):
        return self.json_field.get_lookup(lookup_name)

    def get_transform(self, lookup_name):
        return self.json_field.get_transform(lookup_name)

    def deconstruct(self):
        name, path, _, kwargs = super().deconstruct()
        lookup = BlockDefinitionLookupBuilder()
        block_types = [
            (name, lookup.add_block(block))
            for name, block in self.stream_block.child_blocks.items()
        ]
        args = [block_types]
        kwargs["block_lookup"] = lookup.get_lookup_as_dict()
        return name, path, args, kwargs

    def to_python(self, value):
        result = self.stream_block.to_python(value)

        # The top-level StreamValue is passed a reference to the StreamField, to support
        # pickling. This is necessary because unpickling needs access to the StreamBlock
        # definition, which cannot itself be pickled; instead we store a pointer to the
        # field within the model, which gives us a path to retrieve the StreamBlock definition.
        result._stream_field = self
        return result

    def get_prep_value(self, value):
        if (
            isinstance(value, StreamValue)
            and not (value)
            and value.raw_text is not None
        ):
            # An empty StreamValue with a nonempty raw_text attribute should have that
            # raw_text attribute written back to the db. (This is probably only useful
            # for reverse migrations that convert StreamField data back into plain text
            # fields.)
            return value.raw_text
        elif isinstance(value, StreamValue):
            # StreamValue instances must be prepared first.
            return json.dumps(
                self.stream_block.get_prep_value(value), cls=DjangoJSONEncoder
            )
        else:
            # When querying with JSONField features, the rhs might not be a StreamValue.
            # Note: when Django 4.2 is the minimum supported version, this can be removed
            # as the serialisation is handled in get_db_prep_value instead.
            return self.json_field.get_prep_value(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        if not isinstance(value, StreamValue):
            # When querying with JSONField features, the rhs might not be a StreamValue.
            # As of Django 4.2, JSONField value serialisation is handled in
            # get_db_prep_value instead of get_prep_value.
            return self.json_field.get_db_prep_value(value, connection, prepared)
        return super().get_db_prep_value(value, connection, prepared)

    def from_db_value(self, value, expression, connection):
        if isinstance(expression, KeyTransform):
            # This could happen when using JSONField key transforms,
            # e.g. Page.object.values('body__0').
            try:
                # We might be able to properly resolve to the appropriate StreamValue
                # based on `expression` and `self.stream_block`, but it might be too
                # complicated to do so. For now, just deserialise the value.
                return json.loads(value)
            except ValueError:
                # Just in case the extracted value is not valid JSON.
                return value

        return self.to_python(value)

    def formfield(self, **kwargs):
        """
        Override formfield to use a plain forms.Field so that we do no transformation on the value
        (as distinct from the usual fallback of forms.CharField, which transforms it into a string).
        """
        defaults = {"form_class": BlockField, "block": self.stream_block}
        defaults.update(kwargs)
        return super().formfield(**defaults)

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)

    def get_searchable_content(self, value):
        return self.stream_block.get_searchable_content(value)

    def extract_references(self, value):
        yield from self.stream_block.extract_references(value)

    def get_block_by_content_path(self, value, path_elements):
        """
        Given a list of elements from a content path, retrieve the block at that path
        as a BoundBlock object, or None if the path does not correspond to a valid block.
        """
        return self.stream_block.get_block_by_content_path(value, path_elements)

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(self.stream_block.check(field=self, **kwargs))
        return errors

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)

        # Add Creator descriptor to allow the field to be set from a list or a
        # JSON string.
        setattr(cls, self.name, Creator(self))
