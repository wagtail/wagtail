import json
import re
from itertools import chain
from warnings import warn

from django.apps import apps
from django.contrib.admin.utils import NestedObjects
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.models import CASCADE, DO_NOTHING, PROTECT, SET_DEFAULT, SET_NULL, Model, Q
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from taggit.models import TaggedItemBase

from wagtail.core.blocks import (
    Block, ChooserBlock, ListBlock, RichTextBlock, StreamBlock, StructBlock)
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.rich_text import RichText, features
from wagtail.core.rich_text.rewriters import FIND_A_TAG, FIND_EMBED_TAG, extract_attrs


def get_obj_base_key(obj):
    """
    Returns a simple immutable value to easily hash model instances.

    This allows time and memory efficient object comparisons.
    """
    # base model = the non-abstract model class highest up the inheritance chain
    base_model = ([obj._meta.model] + obj._meta.get_parent_list())[-1]
    return base_model._meta.label, obj.pk


def find_objects_in_rich_text(rich_text: str):
    """
    Yields all ``Model`` instance references within
    a ``RichTextField`` or ``RichTextBlock`` string value.

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
            try:
                instance = handler.get_instance(attrs)
                yield instance
            except (ObjectDoesNotExist, NotImplementedError):
                # Ignore links/embeds that fail to resolve to a currently-existing object,
                # or do not correspond to a model at all
                pass


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
        self.db_vendor = connections[using].vendor

    @staticmethod
    def get_handlers(searched_objects):
        """Given a collection of model instances, yield a sequence of (model, handler) tuples
        that define ways those models may be represented as links or embeds in rich text"""
        searched_models = set()
        for obj in searched_objects:
            searched_models.add(obj._meta.model)
            searched_models.update(obj._meta.get_parent_list())

        for handler in chain(features.get_link_types().values(),
                             features.get_embed_types().values()):
            try:
                model = handler.get_model()
            except NotImplementedError:
                continue

            if model in searched_models:
                yield model, handler

    @staticmethod
    def get_all_handlers():
        """Yield a sequence of (model, handler) tuples for all of the link / embed types that
        represent model instances within rich text"""
        for handler in chain(features.get_link_types().values(),
                             features.get_embed_types().values()):
            try:
                model = handler.get_model()
            except NotImplementedError:
                continue

            yield model, handler

    @staticmethod
    def get_type_attribute_pattern(handlers):
        """Return a regular expression pattern that matches the linktype/embedtype attribute of a
        pseudo-HTML tag produced by any of the given link/embed handlers"""
        # form a list of the identifiers that these handlers use as the linktype/embedtype attribute;
        # e.g. ['page', 'image', 'document']
        link_types = [re.escape(h.identifier) for h in handlers.values()]

        # if there is only one link_type, the resulting pattern will be of the form '(link|embed)type="page"';
        # if there are multiple, it will be of the form '(link|embed)type="(page|image)"'
        return r'(link|embed)type="%s"' % (
            link_types[0] if len(link_types) == 1
            else r'(%s)' % r'|'.join(link_types))

    def get_pattern_for_objects(self, searched_objects):
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
        will also be yielded.
        """
        handlers = dict(self.get_handlers(searched_objects))
        if not handlers:
            return

        # The overall structure of a matching link/embed tag: an 'a' or 'embed' tag, with attributes
        # for the type and value (which will be constructed below as separate patterns and interpolated
        # into the final pattern), in either order. These may optionally be followed by additional
        # attributes before the closing bracket of the tag.
        pattern = r'<(a|embed)( %(type)s %(val)s| %(val)s %(type)s)[^>]*>'

        params = {'type': self.get_type_attribute_pattern(handlers)}

        values = []
        for obj in searched_objects:
            # find the link/embed handlers corresponding to this object's model
            for model, handler in handlers.items():
                if isinstance(obj, model):
                    # query the handler for the attribute name/value that identifies this object
                    # (this varies between handlers; e.g. media embeds use url rather than id)
                    k, v = handler.get_id_pair_from_instance(obj)
                    values.append('%s="%s"' % (k, re.escape(str(v))))

        # if multiple value attributes are to be matched, join them into a (val1|val2|val3) expression
        params['val'] = (values[0] if len(values) == 1
                         else r'(%s)' % r'|'.join(values))

        # Modify the overall pattern to permit additional arbitrary attributes before and between
        # the type / value attributes; then interpolate the patterns for the type / value attributes
        # to produce the final pattern.
        if self.db_vendor == 'mysql':
            return pattern.replace(r' ', r'[^>]*[[:space:]]') % params
        else:
            return pattern.replace(r' ', r'[^>]*\s') % params

    def get_pattern_for_all_objects(self):
        """
        Return a regular expression pattern to match rich text strings that contain link/embed references
        to any model instances.
        This pattern may be overly eager; i.e. it may produce false positives where a string matches
        but does not in fact contain object references. (For performance, this should be minimised as
        much as possible.) However, it must not fail to match any strings that _do_ contain object
        references.
        """
        handlers = dict(self.get_all_handlers())
        if not handlers:
            return

        params = {'type': self.get_type_attribute_pattern(handlers)}
        pattern = r'<(a|embed) %(type)s[^>]*>'

        # Modify the overall pattern to permit additional arbitrary attributes before the type
        # attribute; then interpolate the pattern for the type attribute to produce the final pattern.
        if self.db_vendor == 'mysql':
            return pattern.replace(r' ', r'[^>]*[[:space:]]') % params
        else:
            return pattern.replace(r' ', r'[^>]*\s') % params

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

        # Form the regular expression pattern to match each rich text field against
        pattern = self.get_pattern_for_objects(searched_objects)
        if pattern is None:
            return

        # form a Q expression to perform a regexp match against all rich text fields of this model,
        # ORed together
        filters = Q()
        for field in self.fields:
            filters |= Q(**{field.attname + '__regex': pattern})

        # Form a set of (model, id) tuples that unambiguously represent the models being searched for
        searched_data = {get_obj_base_key(obj) for obj in searched_objects}

        for obj in self.model._default_manager.using(self.using) \
                .filter(filters):
            # for each instance that matched the regexp pattern (which may include false positives),
            # perform a systematic scan of all objects referenced in that instance's rich text fields
            for field in self.fields:
                for found_obj in find_objects_in_rich_text(
                        getattr(obj, field.attname)):
                    # check if this object is one we're searching for, by comparing on base_key
                    if get_obj_base_key(found_obj) in searched_data:
                        yield obj, found_obj

    def find_all_objects(self):
        """Yield a sequence of (this_object, found_object) tuples for all objects referenced as
        links/embeds within rich text fields of this model."""
        if not self.fields:
            return

        # Form the regular expression pattern to match each rich text field against
        pattern = self.get_pattern_for_all_objects()
        if pattern is None:
            return

        # form a Q expression to perform a regexp match against all rich text fields of this model,
        # ORed together
        filters = Q()
        for field in self.fields:
            filters |= Q(**{field.attname + '__regex': pattern})

        for obj in self.model._default_manager.using(self.using) \
                .filter(filters):
            # for each instance that matched the regexp pattern (indicating that it contained linked/embedded
            # objects of any type), unpack all objects referenced in that instance's rich text fields
            for field in self.fields:
                for found_obj in find_objects_in_rich_text(
                        getattr(obj, field.attname)):
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
        [['StreamBlock', 'CharBlock'], ['StreamBlock', 'ListBlock', 'TextBlock']]
        """
        for block_path in self.block_tree_paths(self.field.stream_block):
            if isinstance(block_path[-1], block_types):
                yield block_path

    def find_objects(self, value, block_path):
        """
        Recursively traverse a StreamField value to find all sub-values corresponding to
        the given block path, and yield all model instances found within those sub-values.

        :param value: A value existing at any level of ``StreamField`` data. The type of
            this value must match the first item in ``block_path``.
        :param block_path: The path to a block, as a tuple of block definition objects.
        """
        current_block, *remaining_path = block_path

        if not remaining_path:
            # End of path reached; return model instances found within `value`
            if isinstance(value, RichText):
                # descend into rich text value and yield objects found within it
                yield from find_objects_in_rich_text(value.source)
            elif isinstance(value, Model):
                yield value
        else:
            if isinstance(current_block, ListBlock):
                if value is not None:
                    # all child values of a ListBlock satisfy block_path; iterate over all of them
                    for child_value in value:
                        yield from self.find_objects(child_value, remaining_path)
            elif isinstance(current_block, StructBlock):
                # the next block in block_path indicates an item within this value (a dict) to
                # be traversed
                child_block_name = remaining_path[0].name
                try:
                    child_value = value[child_block_name]
                except (KeyError, TypeError):
                    # value is None or does not contain child_block_name; stop traversing
                    return

                yield from self.find_objects(child_value, remaining_path)

            elif isinstance(current_block, StreamBlock):
                # traverse all stream children whose block definitions match the next block in block_path
                child_block = remaining_path[0]

                if value is not None:
                    for stream_child in value:
                        if stream_child.block == child_block:
                            yield from self.find_objects(stream_child.value, remaining_path)
            else:
                warn("Unexpected StreamField block: don't know how to traverse %r (value: %r)"
                     % (current_block, str(value)[:30]))


class ModelStreamFieldsCollector:
    """Handles searches for object references across all StreamFields of a model"""
    def __init__(self, model, using=DEFAULT_DB_ALIAS):
        self.model = model
        self.using = using
        self.fields = [field for field in model._meta.fields
                       if isinstance(field, StreamField)]
        self.field_collectors = [StreamFieldCollector(field)
                                 for field in self.fields]
        self.rich_text_collector = ModelRichTextCollector(model, using=using)
        self.db_vendor = connections[using].vendor

    def find_objects(self, *searched_objects, block_types: tuple = ()):
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
        if not searched_objects:
            return
        if not block_types:
            # define the list of block types that may contain object references;
            # choosers and rich text, by default
            block_types = (ChooserBlock, RichTextBlock)

        # find all occurrences of these block types across all StreamFields of the model;
        # store each one as a tuple of StreamFieldCollector (which identifies a single field)
        # and path to the block (a list of ancestor blocks)
        block_paths_per_collector = [(c, list(c.find_block_type(block_types)))
                                     for c in self.field_collectors]

        # Construct a regexp pattern that matches any of the searched objects in the format
        # we expect to see them when they appear directly in stream data (i.e. not within
        # rich text); This consists of:
        # - the object's primary key, JSON-encoded (to account for non-numeric keys)
        # - appearing as a value within a dict or array, i.e. preceded by `[`, `:`, `,` or whitespace and followed by `]`, `}`, `,` or whitespace
        object_id_pattern = '|'.join(re.escape(json.dumps(v.pk)) for v in searched_objects)
        if self.db_vendor == 'mysql':
            stream_structure_pattern = r'[[,[:space:]:](%s)[]},[:space:]]' % object_id_pattern
        else:
            stream_structure_pattern = r'[[,\s:](%s)[]},\s]' % object_id_pattern

        rich_text_pattern = self.rich_text_collector.get_pattern_for_objects(searched_objects)
        if rich_text_pattern is None:
            pattern = stream_structure_pattern
        else:
            # Rich text content will appear in JSON-escaped form, so adjust the regexp
            # pattern to compensate, by searching for backslash-escaped double quotes
            # where we would previously have searched for unescaped ones
            rich_text_pattern = rich_text_pattern.replace(r'"', r'\\"')

            # Final pattern shall match stream_structure_pattern OR rich_text_pattern
            pattern = r'(%s|%s)' % (stream_structure_pattern, rich_text_pattern)

        # Generate a filter expression that will find records where any StreamField
        # field matches:
        # * the above regexp pattern for the PK value(s)
        # * AND a (quoted) block name that indicates the presence of a block that can contain
        #   object references, as specified by block_types above
        filters = Q()
        for collector, block_paths in block_paths_per_collector:
            field_name = collector.field.attname

            # for each block in the StreamField's definition that might contain an object
            # reference, as specified by block_types above, find the deepest-nested named
            # block in its path. (Not all blocks are named; the child block of a ListBlock
            # isn't, for example.)
            last_blocks = [[block for block in block_path if block.name][-1]
                           for block_path in block_paths]
            block_filter = Q(**{field_name + '__regex': r'"(%s)"'
                                % '|'.join({block.name for block in last_blocks})})
            value_filter = (
                Q(**{field_name + '__regex': pattern})
                if searched_objects else Q())
            filters |= block_filter & value_filter

        searched_data = {get_obj_base_key(v) for v in searched_objects}

        # look for candidate objects matching on these regexp filters
        for obj in self.model._default_manager.using(self.using) \
                .filter(filters):
            # for each candidate object, invoke a StreamFieldCollector on each StreamField defined on the model
            for collector, block_paths in block_paths_per_collector:
                # Check each block path where object references may be found
                for block_path in block_paths:
                    for found_value in collector.find_objects(
                            getattr(obj, collector.field.attname), block_path):
                        # Yield value if it's one of the objects we're searching for
                        if get_obj_base_key(found_value) in searched_data:
                            yield obj, found_value


class Use:
    """
    Identifies a place where a model instance has been referenced from another object, and the
    on_delete behaviour of that relation
    """
    def __init__(self, obj: Model, parent=None, on_delete=CASCADE, field=None):
        self.object = obj  # object containing the reference
        self.key = get_obj_base_key(obj)
        self.on_delete = on_delete
        self.field = field

        # number of CASCADE steps away from the immediate object being deleted
        self.depth = 0 if parent is None else parent.depth + 1

    @classmethod
    def from_flat_iterable(cls, iterable, on_delete=CASCADE, field=None,
                           exclude=None):
        """
        Given a sequence of model instances, yield a sequence of Use records
        wrapping those instances. The sequence of models will be de-duplicated.

        :param iterable: Iterable sequence of model instances
        :param on_delete: on_delete behaviour to assign to the Use records
        :param field: field identifier to assign to the Use records
        :param exclude: Set of Use records to omit from the returned sequence. Will be modified in-place to include all returned records
        """
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
        """
        Given a sequence of model instances, which may contain sub-lists indicating cascading deletions,
        yield a sequence of Use records.

        ``nested_list`` is a complicated data structure returned by ``NestedObjects.nested()``.
        The root contains all the objects passed in ``NestedObjects, as well as some related objects.
        Suppose we have multiple items:
        - ``original1`` & ``original2``, the originals we want to delete
        - ``m2m11`` & ``m2m12``, two many-to-many items from ``original1``
        - ``m2m21``, a many-to-many item from ``original2``
        - ``related_fk``, an item that has a foreign key pointing to ``origina1``
        - ``one_to_one``, an item that has a one_to_one pointing from or to ``original1``
        - ``related_gfk``, an item that has a generic foreign key pointing to ``original1``
        Then ``nested_list`` will be:
        [original1, [m2m11, m2m12, related_fk], original2, [m2m21], one_to_one, related_gfk]

        :param nested_list: Iterable sequence of model instances; may contain sub-lists which indicate
            cascading deletions from the previous model instance in the sequence
        :param parent: For cascading deletions, the Use record to assign as the parent
        :param on_delete: on_delete behaviour to assign to the Use records
        :param exclude: Set of Use records to omit from the returned sequence. Will be modified
            in-place to include all returned records
        :param originals: List of original instances which we're finding references to, as opposed to ones which
            appear in ``nested_list`` as part of a CASCADE chain
        """
        if exclude is None:
            exclude = set(originals)

        # Retain the Use record for the most-recently-handled instance, as this will be used as the parent
        # for any sub-lists we encounter
        parent_use = None

        for obj in nested_list:
            if isinstance(obj, list):
                yield from cls.from_nested_list(
                    obj, parent=parent_use, on_delete=on_delete, exclude=exclude)
            else:
                use = cls(obj, parent=parent, on_delete=on_delete)
                # When ``use`` was already listed, we don’t want to list it
                # but we want to mark it as parent of the next item, in case
                # that next item is a list.
                if use in exclude:
                    # When ``use`` is in ``originals``, we don’t want
                    # to mark it as parent of the next item because we want
                    # to display the next item as root, otherwise the first
                    # level of deleted objects would be shown nested.
                    if use in originals:
                        parent_use = None
                        continue
                    # Finds the already existing instance of ``Use``
                    # for ``obj`` in ``exclude``
                    # to avoid increasing RAM usage.
                    for other_use in exclude:
                        if use == other_use:
                            parent_use = other_use
                            break
                else:
                    exclude.add(use)
                    yield use
                    parent_use = use

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return isinstance(other, Use) and self.key == other.key

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
                           ('\u00A0' * self.depth * 8), html)

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
    paginator = Paginator(uses, per_page=20)
    page = paginator.get_page(request.GET.get('p'))
    page.are_protected = are_protected
    return page
