from collections import defaultdict

import factory
from factory.declarations import ParameteredAttribute

from wagtail import blocks
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock

from .builder import (
    ListBlockStepBuilder,
    StreamBlockStepBuilder,
    StructBlockStepBuilder,
)
from .factories import DocumentFactory, ImageFactory, PageFactory
from .options import BlockFactoryOptions, StreamBlockFactoryOptions

__all__ = [
    "CharBlockFactory",
    "IntegerBlockFactory",
    "StreamBlockFactory",
    "StreamFieldFactory",
    "ListBlockFactory",
    "StructBlockFactory",
    "PageChooserBlockFactory",
    "ImageChooserBlockFactory",
    "DocumentChooserBlockFactory",
]


class StreamBlockFactory(factory.Factory):
    _options_class = StreamBlockFactoryOptions
    _builder_class = StreamBlockStepBuilder

    @classmethod
    def _generate(cls, strategy, params):
        if cls._meta.abstract and not hasattr(cls, "__generate_abstract__"):
            raise factory.errors.FactoryError(
                "Cannot generate instances of abstract factory %(f)s; "
                "Ensure %(f)s.Meta.model is set and %(f)s.Meta.abstract "
                "is either not set or False." % {"f": cls.__name__}
            )
        step = cls._builder_class(cls._meta, params, strategy)
        return step.build()

    @classmethod
    def _construct_stream(cls, block_class, *args, **kwargs):
        def get_index(key):
            return int(key.split(".")[0])

        stream_length = max(map(get_index, kwargs.keys())) + 1 if kwargs else 0
        stream_data = [None] * stream_length
        for indexed_block_name, value in kwargs.items():
            i, name = indexed_block_name.split(".")
            stream_data[int(i)] = (name, value)

        block_def = cls._meta.get_block_definition()
        if block_def is None:
            # We got an old style definition, so aren't aware of a StreamBlock class for the
            # StreamField's child blocks. As nesting of StreamBlocks isn't supported for this
            # kind of declaration, returning the stream data without up-casting it to a
            # StreamValue is OK here. StreamField handles conversion to a StreamValue, but not
            # recursively.
            return stream_data
        return blocks.StreamValue(block_def, stream_data)

    @classmethod
    def _build(cls, block_class, *args, **kwargs):
        return cls._construct_stream(block_class, *args, **kwargs)

    @classmethod
    def _create(cls, block_class, *args, **kwargs):
        return cls._construct_stream(block_class, *args, **kwargs)

    class Meta:
        abstract = True


class StreamFieldFactory(ParameteredAttribute):
    """
    Syntax:
        <streamfield>__<index>__<block_name>__<key>='foo',

    Syntax to generate blocks with default factory values:
        <streamfield>__<index>=<block_name>

    """

    def __init__(self, block_types, **kwargs):
        super().__init__(**kwargs)
        if isinstance(block_types, dict):
            # Old style definition, dict mapping block name -> block factory
            self.stream_block_factory = type(
                "_GeneratedStreamBlockFactory",
                (StreamBlockFactory,),
                {**block_types, "__generate_abstract__": True},
            )
        elif isinstance(block_types, type) and issubclass(
            block_types, StreamBlockFactory
        ):
            block_types._meta.block_def = block_types._meta.model()
            self.stream_block_factory = block_types
        else:
            raise TypeError(
                "StreamFieldFactory argument must be a StreamBlockFactory subclass or dict "
                "mapping block names to factories"
            )

    def evaluate(self, instance, step, extra):
        return self.stream_block_factory(**extra)


class ListBlockFactory(factory.SubFactory):
    _builder_class = ListBlockStepBuilder

    def __call__(self, **kwargs):
        return self.evaluate(None, None, kwargs)

    def evaluate(self, instance, step, extra):
        result = defaultdict(dict)
        for key, value in extra.items():
            if key.isdigit():
                result[int(key)]["value"] = value
            else:
                prefix, label = key.split("__", maxsplit=1)
                if prefix and prefix.isdigit():
                    result[int(prefix)][label] = value

        subfactory = self.get_factory()
        force_sequence = step.sequence if self.FORCE_SEQUENCE else None
        values = [
            step.recurse(subfactory, params, force_sequence=force_sequence)
            for _, params in sorted(result.items())
        ]

        list_block_def = blocks.list_block.ListBlock(subfactory._meta.model())
        return blocks.list_block.ListValue(list_block_def, values)


class StructBlockFactory(factory.Factory):
    _options_class = BlockFactoryOptions
    _builder_class = StructBlockStepBuilder

    class Meta:
        abstract = True
        model = blocks.StructBlock

    @classmethod
    def _construct_struct_value(cls, block_class, params):
        return blocks.StructValue(
            block_class(),
            [(name, value) for name, value in params.items()],
        )

    @classmethod
    def _build(cls, block_class, *args, **kwargs):
        return cls._construct_struct_value(block_class, kwargs)

    @classmethod
    def _create(cls, block_class, *args, **kwargs):
        return cls._construct_struct_value(block_class, kwargs)


class BlockFactory(factory.Factory):
    _options_class = BlockFactoryOptions
    _builder_class = factory.builder.StepBuilder

    class Meta:
        abstract = True

    @classmethod
    def _construct_block(cls, block_class, *args, **kwargs):
        if kwargs.get("value"):
            return block_class().clean(kwargs["value"])
        return block_class().get_default()

    @classmethod
    def _build(cls, block_class, *args, **kwargs):
        return cls._construct_block(block_class, *args, **kwargs)

    @classmethod
    def _create(cls, block_class, *args, **kwargs):
        return cls._construct_block(block_class, *args, **kwargs)


class CharBlockFactory(BlockFactory):
    class Meta:
        model = blocks.CharBlock


class IntegerBlockFactory(BlockFactory):
    class Meta:
        model = blocks.IntegerBlock


class ChooserBlockFactory(BlockFactory):
    pass


class PageChooserBlockFactory(ChooserBlockFactory):
    page = factory.SubFactory(PageFactory)

    class Meta:
        model = blocks.PageChooserBlock

    @classmethod
    def _build(cls, model_class, page):
        return page

    @classmethod
    def _create(cls, model_class, page):
        return page


class ImageChooserBlockFactory(ChooserBlockFactory):
    image = factory.SubFactory(ImageFactory)

    class Meta:
        model = ImageChooserBlock

    @classmethod
    def _build(cls, model_class, image):
        return image

    @classmethod
    def _create(cls, model_class, image):
        return image


class DocumentChooserBlockFactory(ChooserBlockFactory):
    document = factory.SubFactory(DocumentFactory)

    class Meta:
        model = DocumentChooserBlock

    @classmethod
    def _build(cls, model_class, document):
        return document

    @classmethod
    def _create(cls, model_class, document):
        return document
