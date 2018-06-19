import re
from itertools import chain
from warnings import warn

from django.apps import apps
from django.contrib.admin.utils import NestedObjects
from django.db import DEFAULT_DB_ALIAS
from django.db.models import CASCADE, DO_NOTHING, PROTECT, SET_DEFAULT, SET_NULL, Model, Q
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from taggit.models import TaggedItemBase

from wagtail.core.blocks import (
    Block, ChooserBlock, ListBlock, RichTextBlock, StreamBlock, StreamValue,
    StructBlock, StructValue,
)
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.rich_text import RichText, features
from wagtail.core.rich_text.rewriters import FIND_A_TAG, FIND_EMBED_TAG, extract_attrs
from wagtail.utils.pagination import paginate


def get_obj_base_key(obj):
    """
    Returns a simple immutable value to easily hash model instances.

    This allows time and memory efficient object comparisons.
    """
    if isinstance(obj, Model):
        base_model = ([obj._meta.model] + obj._meta.get_parent_list())[-1]
        return base_model._meta.label, obj.pk
    return obj


def find_objects_in_rich_text(rich_text: str):
    """
    Yields all ``Model`` instance references within
    a ``RichTextField`` or ``RichTextBlock`` value.

    It finds items included as links (like ``Page`` & ``Document`` objects)
    as well as those included as embeds (like ``Image`` & ``Embed`` objects).
    """
    for regex, registry, name_attr in (
            (FIND_A_TAG, features.get_link_types(), 'linktype'),
            (FIND_EMBED_TAG, features.get_embed_types(), 'embedtype')):
        for attr_string in regex.findall(rich_text):
            attrs = extract_attrs(attr_string)
            if name_attr not in attrs:
                continue
            handler = registry[attrs[name_attr]]
            instance = handler.get_instance(attrs)
            if instance is not None:
                yield instance


class ModelRichTextCollector:
    """
    ``ModelRichTextCollector`` helps finding all the ``Model`` instances
    contained within all the ``RichTextField``s of the ``Model`` subclass
    passed in the initializer of that class.
    """
    def __init__(self, model, using: str = DEFAULT_DB_ALIAS):
        self.model = model
        self.using = using
        self.fields = [f for f in self.model._meta.fields
                       if isinstance(f, RichTextField)]

    @staticmethod
    def get_handlers(searched_objects):
        """
        Yields the link and embed handlers used in ``RichTextField``
        and ``RichTextBlock`` to embed related objects within text.

        It only yields the handlers relevant to ``searched_objects``.
        So if none of the objects can be included in rich text,
        nothing will be yield.
        """
        if searched_objects:
            searched_models = set()
            for obj in searched_objects:
                searched_models.add(obj._meta.model)
                searched_models.update(obj._meta.get_parent_list())

        for handler in chain(features.get_link_types().values(),
                             features.get_embed_types().values()):
            model = handler.get_model()
            if searched_objects:
                if model in searched_models:
                    yield model, handler
            else:
                yield model, handler

    @classmethod
    def get_pattern_for_objects(cls, searched_objects):
        """
        Returns the regular expression pattern that will match any type of
        inclusion of any of the ``searched_objects``.

        This pattern will allow to quickly identify candidates that have
        a ``RichText`` containing at least one of the ``searched_objects``.
        It can give false positives since ``find_objects_in_rich_text`` is used
        to double check that one of the ``searched_objects`` is actually
        contained in the candidate rich text. However, this pattern must never
        skip candidates.

        In short, this pattern allows to find database relations through
        a rich text with 100% accuracy without having to iterate in Python
        over all rich text values. In some cases it is possible
        that invalid candidates are found with this pattern, for example when
        ``searched_objects`` contains ``(Document(pk=1), Image(pk=2))``,
        candidates containing ``Image(pk=1)`` and ``Document(pk=2)``
        will also be yield.
        """
        handlers = dict(cls.get_handlers(searched_objects))
        if not handlers:
            return

        link_types = [re.escape(h.link_type) for h in handlers.values()]
        type_pat = r'(link|embed)type="%s"' % (
            link_types[0] if len(link_types) == 1
            else r'(%s)' % r'|'.join(link_types))
        params = {'type': type_pat}
        if searched_objects:
            pattern = r'<(a|embed)( %(type)s %(val)s| %(val)s %(type)s)[^>]*>'
            values = []
            for obj in searched_objects:
                for model, handler in handlers.items():
                    if isinstance(obj, model):
                        k, v = handler.get_id_pair_from_instance(obj)
                        values.append('%s="%s"' % (k, re.escape(str(v))))
            params['val'] = (values[0] if len(values) == 1
                             else r'(%s)' % r'|'.join(values))
        else:
            pattern = r'<(a|embed) %(type)s[^>]*>'
        return pattern.replace(r' ', r'[^>]*[ \t\n]') % params

    def find_objects(self, *searched_objects):
        """
        Yields all ``self.model`` instances containing at least one
        of the ``searched_objects`` in one of its ``RichTextField``s.

        This methods uses ``get_pattern_for_objects`` to identify
        candidates, then ``find_objects_in_rich_text`` to actually fetch
        the objects and remove the false positives yield by the pattern.

        This generator yields a ``tuple`` of two values:
        first the ``self.model`` instance with the ``RichTextField``,
        and then the object from ``searched_objects`` that was found
        in this ``RichTextField``.

        To search for all the relations contained in all the ``RichTextField``s
        of all the instances of ``self.model``, use that method
        without argument.

        :param searched_objects: ``Model`` instances that will be searched
                                 within all ``RichTextField``s.
        """
        if not self.fields:
            return

        pattern = self.get_pattern_for_objects(searched_objects)
        if pattern is None:
            return

        filters = Q()
        for field in self.fields:
            filters |= Q(**{field.attname + '__regex': pattern})

        searched_data = {get_obj_base_key(obj) for obj in searched_objects}
        for obj in self.model._default_manager.using(self.using) \
                .filter(filters):
            for field in self.fields:
                for found_obj in find_objects_in_rich_text(
                        getattr(obj, field.attname)):
                    if not searched_objects or \
                            get_obj_base_key(found_obj) in searched_data:
                        yield obj, found_obj


class StreamFieldCollector:
    """
    ``StreamFieldCollector`` helps ``StreamField`` introspection for:

    - locating blocks of specified types in a ``StreamField`` architecture
    - finding all the values for a specific path

    In this whole class, by “path” we mean the path inside the structure
    of a ``StreamField`` **instance**. Do not confuse it with the path
    inside the structure of a ``StreamField`` **value**.

    Note that paths don’t include the name given to block instances, because
    not all block types have a name (e.g. the child of
    a ``ListBlock`` instance), and the ones with a name store it
    as their ``name`` attribute.
    """

    def __init__(self, field):
        self.field = field

    def block_tree_paths(self, block: Block, ancestors: tuple = ()):
        """
        Recursive generator yielding all paths that start with ``block``
        in the ``StreamField`` of this collector, ``self.field``.

        A path is a ``tuple`` containing all the ``Block`` instances leading to
        a ``Block`` instance that is a leaf of the tree.

        Example:

        >>> from wagtail.core.blocks import CharBlock
        >>> from wagtail.core.fields import StreamField
        >>> stream_field = StreamField([
        ...     ('title', CharBlock()),
        ...     ('items', ListBlock(CharBlock())),
        ... ])
        >>> [[b.__class__.__name__ for b in path]
        ...  for path in StreamFieldCollector(stream_field)
        ...              .block_tree_paths(stream_field.stream_block)]
        [['StreamBlock', 'CharBlock'], ['StreamBlock', 'ListBlock', 'CharBlock']]
        """
        if isinstance(block, (StreamBlock, StructBlock)):
            for child_block in block.child_blocks.values():
                yield from self.block_tree_paths(child_block,
                                                 ancestors + (block,))
        elif isinstance(block, ListBlock):
            yield from self.block_tree_paths(block.child_block,
                                             ancestors + (block,))
        else:
            yield ancestors + (block,)

    def find_block_type(self, block_types):
        """
        Yields all the possible paths for ``Block`` instances of one of the
        ``Block`` subclasses passed as the ``block_types``.

        Example:

        >>> from wagtail.core.blocks import CharBlock, TextBlock
        >>> from wagtail.core.fields import StreamField
        >>> stream_field = StreamField([
        ...     ('title', CharBlock()),
        ...     ('items', ListBlock(TextBlock())),
        ... ])
        >>> [[b.__class__.__name__ for b in path]
        ...  for path in StreamFieldCollector(stream_field)
        ...              .find_block_type((CharBlock, TextBlock))]
        [['StreamBlock', 'ListBlock', 'TextBlock']]
        """
        for block_path in self.block_tree_paths(self.field.stream_block):
            if isinstance(block_path[-1], block_types):
                yield block_path

    def find_values(self, stream, block_path: tuple):
        """
        Recursive generator yielding all values found
        for a given ``block_path``.

        :param stream: ``StreamField`` value, regardless of its level
            in the tree. It can be a ``StreamValue``, ``StructValue``, or any
            data that can be contained by any type of ``Block``, leaf or not.
        :param block_path: Tuple containing the path to a block.
        """
        if not block_path:
            if isinstance(stream, RichText):
                yield from find_objects_in_rich_text(stream.source)
            else:
                yield stream
            return
        current_block, *block_path = block_path
        if isinstance(current_block, StreamBlock) \
                and isinstance(stream, StreamValue):
            for sub_value in stream:
                yield from self.find_values(sub_value, block_path)
        elif isinstance(stream, StreamValue.StreamChild):
            if stream.block == current_block:
                yield from self.find_values(stream.value, block_path)
        elif isinstance(stream, StructValue):
            if current_block.name in stream:
                yield from self.find_values(stream[current_block.name],
                                            block_path)
        elif current_block.name == '' and isinstance(stream, list):
            for sub_value in stream:
                yield from self.find_values(sub_value, block_path)
        else:
            warn('Unexpected StreamField value: <%s: %s>'
                 % (type(stream), str(stream)[:30]))


class ModelStreamFieldsCollector:
    def __init__(self, model, using=DEFAULT_DB_ALIAS):
        self.model = model
        self.using = using
        self.fields = [field for field in model._meta.fields
                       if isinstance(field, StreamField)]
        self.field_collectors = [StreamFieldCollector(field)
                                 for field in self.fields]

    def prepare_value(self, value) -> str:
        """
        Transforms a value from Python to the storage format
        of ``StreamField``. It is close to JSON, except that multiple values
        can be stored as a PIPE separated string.
        """
        if isinstance(value, Model):
            return str(value.pk)
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if value is None:
            return 'null'
        return '"%s"' % re.escape(str(value).replace('"', r'\"')
                                  .replace('|', r'\|'))

    def find_objects(self, *searched_values, block_types: tuple = ()):
        """
        Yields all ``self.model`` instances that contain at least one
        of the ``searched_values`` inside one of its ``StreamField``s.

        This generator yields a tuple of two values: first, the ``self.model``
        instance with the ``StreamField``, and then the value
        or ``Model`` instance that was found in that ``StreamField``.

        By default, only ``Model`` instances or primary keys can be searched.
        To search for other types, fill ``block_types``.

        This method also searches ``Model`` instances nested inside
        ``RichTextBlock``s at any depth.

        :param searched_values: Values of any type that can be contained
            in a ``StreamField``, including ``Model`` instances.
        :param block_types: ``Block`` subclasses to search for,
                            or any type if empty.
        """
        if not self.fields:
            return
        if not block_types:
            block_types = (ChooserBlock, RichTextBlock)
        block_paths_per_collector = [(c, list(c.find_block_type(block_types)))
                                     for c in self.field_collectors]
        stream_structure_pattern = r'[[ \t\n:](%s)[] \t\n,}]' % '|'.join(
            self.prepare_value(v) for v in searched_values)
        rich_text_pattern = ModelRichTextCollector.get_pattern_for_objects(
            [v for v in searched_values if isinstance(v, Model)])
        if rich_text_pattern is None:
            pattern = stream_structure_pattern
        else:
            # Escapes the pattern since values are between double quotes.
            rich_text_pattern = rich_text_pattern.replace(r'"', r'\\"')
            pattern = r'(%s|%s)' % (stream_structure_pattern, rich_text_pattern)
        filters = Q()
        for collector, block_paths in block_paths_per_collector:
            field_name = collector.field.attname
            last_blocks = [[block for block in block_path if block.name][-1]
                           for block_path in block_paths]
            block_filter = Q(**{field_name + '__regex': r'"(%s)"'
                                % '|'.join({block.name for block in last_blocks})})
            value_filter = (
                Q(**{field_name + '__regex': pattern})
                if searched_values else Q())
            filters |= block_filter & value_filter
        searched_data = {get_obj_base_key(v) for v in searched_values}
        for obj in self.model._default_manager.using(self.using) \
                .filter(filters):
            for collector, block_paths in block_paths_per_collector:
                for block_path in block_paths:
                    for found_value in collector.find_values(
                            getattr(obj, collector.field.attname), block_path):
                        if not searched_values \
                                or get_obj_base_key(found_value) in searched_data:
                            yield obj, found_value


class Use:
    def __init__(self, obj: Model, parent=None, on_delete=CASCADE, field=None):
        self.object = obj
        self.key = get_obj_base_key(obj)
        self.parent = parent
        self.on_delete = on_delete
        self.field = field

        self.depth = 0
        while parent is not None:
            self.depth += 1
            parent = parent.parent

    @classmethod
    def from_flat_iterable(cls, iterable, on_delete=CASCADE, field=None,
                           exclude=None):
        if exclude is None:
            exclude = set()
        for obj in iterable:
            use = cls(obj, on_delete=on_delete, field=field)
            if use not in exclude:
                exclude.add(use)
                yield use

    @classmethod
    def from_nested_list(cls, nested_list, parent=None, on_delete=CASCADE,
                         exclude=None, originals=()):
        if exclude is None:
            exclude = set()
        main_use = None
        for i, obj in enumerate(nested_list):
            if isinstance(obj, list):
                yield from cls.from_nested_list(
                    obj, parent=main_use, on_delete=on_delete, exclude=exclude)
            else:
                use = cls(obj, parent=parent, on_delete=on_delete)
                if use in exclude:
                    if use not in originals:
                        for other_use in exclude:
                            if use == other_use:
                                main_use = other_use
                                break
                else:
                    exclude.add(use)
                    yield use
                    main_use = use

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        if isinstance(other, Use):
            return self.key == other.key
        return self.key == get_obj_base_key(other)

    @property
    def is_root(self):
        return self.depth == 0

    @property
    def is_protected(self):
        return self.on_delete == PROTECT

    def is_hidden(self):
        if self.is_protected:
            return False
        if isinstance(self.object, TaggedItemBase):
            return True
        if hasattr(self.object, 'is_shown_in_uses') \
                and not self.object.is_shown_in_uses():
            return True
        return any(isinstance(field, (ParentalKey, ParentalManyToManyField))
                   for field in self.object._meta.fields)

    def get_on_delete_data(self):
        if self.on_delete == CASCADE:
            return 'serious', _('Will also be deleted')
        if self.on_delete == PROTECT:
            return 'primary', _('Prevents deletion')
        if self.on_delete == SET_NULL:
            if self.field is None:
                return '', _('Field will be emptied')
            return '', _('Field “%s” will be emptied') % self.field.verbose_name
        if self.on_delete == SET_DEFAULT:
            return 'primary', _('Default object will be set')
        if self.on_delete == DO_NOTHING:
            return '', _('Nothing will happen')
        return 'primary', _('Another object will be set')

    def get_on_delete_html(self):
        return format_html('<span class="status-tag {}">{}</span>',
                           *self.get_on_delete_data())

    @property
    def model_name(self):
        return self.object._meta.verbose_name

    def get_edit_link(self):
        from wagtail.admin.viewsets import viewsets

        if hasattr(self.object, 'get_edit_url'):
            url = self.object.get_edit_url()
        else:
            viewset = viewsets.get_for_model(self.object._meta.model)
            if viewset is None:
                return str(self.object)
            url = reverse(viewset.get_url_name('edit'), args=(self.object.pk,))
        return format_html('<a href="{}">{}</a>', url, self.object)

    def get_html(self):
        html = self.get_edit_link()
        if self.is_root:
            return html
        return format_html('{}<i class="icon icon-arrow-right"></i> {}',
                           (' ' * self.depth * 8), html)

    def __html__(self):
        return self.get_html()

    def __repr__(self):
        return '<Use %s pk=%s>' % (self.object.__class__.__name__,
                                   self.object.pk)


def get_all_uses(*objects, using: str = DEFAULT_DB_ALIAS):
    """
    Yields a ``Use`` instance for each ``Model`` instance found that contains
    a relation to any of the ``objects``.

    This function uses three methods to find related objects:

    - the Django collector that inspects ``ForeignKey``s, ``OneToOneField``s,
      ``ManyToManyField``s and ``GenericForeignKey``s
    - the Wagtail rich text collector that inspects ``RichTextField``s
    - the Wagtail ``StreamField`` collector that inspects ``StreamField``,
      including the ``RichTextBlock``s nested within ``StreamField``s
    """
    collector = NestedObjects(using)
    collector.collect(objects)
    originals = {Use(obj) for obj in objects}
    uses = originals.copy()
    yield from Use.from_flat_iterable(collector.protected, on_delete=PROTECT,
                                      exclude=uses)
    yield from Use.from_nested_list(collector.nested(), on_delete=CASCADE,
                                    exclude=uses, originals=originals)
    for relations in collector.field_updates.values():
        for (field, value), related_objects in relations.items():
            yield from Use.from_flat_iterable(
                related_objects, on_delete=field.remote_field.on_delete,
                field=field, exclude=uses)
    for model in apps.get_models():
        yield from Use.from_flat_iterable((
            related_object for related_object, obj in ModelRichTextCollector(
                model, using=using).find_objects(*[u.object for u in uses])),
            on_delete=SET_NULL, exclude=uses)
        yield from Use.from_flat_iterable((
            related_object for related_object, obj in ModelStreamFieldsCollector(
                model, using=using).find_objects(*[u.object for u in uses])),
            on_delete=SET_NULL, exclude=uses)


def get_paginated_uses(request, *objects, using: str = DEFAULT_DB_ALIAS):
    """
    Paginates all the uses found for ``objects`` and provides templates
    an ``are_protected`` attribute to find out if an object prevents deletion.
    """
    uses = list(get_all_uses(*objects, using=using))
    are_protected = any(use.is_protected for use in uses)
    uses = [use for use in uses if not use.is_hidden()]
    page = paginate(request, uses)[1]
    page.are_protected = are_protected
    return page
