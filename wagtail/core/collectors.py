import re
from itertools import chain
from warnings import warn

from django.apps import apps
from django.contrib.admin.utils import NestedObjects
from django.db import DEFAULT_DB_ALIAS
from django.db.models import Model, Q, ProtectedError

from wagtail.core.blocks import (
    ChooserBlock, ListBlock, RichTextBlock, StreamBlock, StreamValue, StructBlock, StructValue)
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.rich_text import (
    EMBED_HANDLERS, FIND_A_TAG, FIND_EMBED_TAG, LINK_HANDLERS, RichText, extract_attrs)
from wagtail.utils.pagination import paginate


def get_obj_base_key(obj):
    if isinstance(obj, Model):
        base_model = ([obj._meta.model] + obj._meta.get_parent_list())[-1]
        return base_model._meta.label, obj.pk
    return obj


def find_objects_in_rich_text(rich_text: str):
    for regex, registry, name_attr in (
            (FIND_A_TAG, LINK_HANDLERS, 'linktype'),
            (FIND_EMBED_TAG, EMBED_HANDLERS, 'embedtype')):
        for attr_string in regex.findall(rich_text):
            attrs = extract_attrs(attr_string)
            if name_attr not in attrs:
                continue
            handler = registry[attrs[name_attr]]
            instance = handler.get_instance(attrs)
            if instance is not None:
                yield instance


class ModelRichTextCollector:
    def __init__(self, model, using=DEFAULT_DB_ALIAS):
        self.model = model
        self.using = using
        self.fields = [f for f in self.model._meta.fields
                       if isinstance(f, RichTextField)]

    @staticmethod
    def get_handlers(searched_objects):
        if searched_objects:
            searched_models = set()
            for obj in searched_objects:
                searched_models.add(obj._meta.model)
                searched_models.update(obj._meta.get_parent_list())

        for handler in chain(LINK_HANDLERS.values(), EMBED_HANDLERS.values()):
            model = handler.get_model()
            if searched_objects:
                if model in searched_models:
                    yield model, handler
            else:
                yield model, handler

    @classmethod
    def get_pattern_for_objects(cls, searched_objects):
        handlers = dict(cls.get_handlers(searched_objects))
        if not handlers:
            return

        handlers_names = [re.escape(h.name) for h in handlers.values()]
        type_pat = r'(link|embed)type="%s"' % (
            handlers_names[0] if len(handlers_names) == 1
            else r'(%s)' % r'|'.join(handlers_names))
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
    def __init__(self, field):
        self.field = field

    def block_tree_paths(self, block, ancestors=()):
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
        for block_path in self.block_tree_paths(self.field.stream_block):
            if isinstance(block_path[-1], block_types):
                yield block_path

    def find_values(self, stream, block_path):
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

    def prepare_value(self, value):
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

    def find_objects(self, *searched_values, block_types=()):
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


def get_all_uses(*objects, using=DEFAULT_DB_ALIAS):
    collector = NestedObjects(using)
    collector.collect(objects)
    keys = {get_obj_base_key(obj) for obj in objects}
    # Prevents an object from being marked as protected by itself
    # due to multi-table inheritance.
    collector.protected = {obj for obj in collector.protected
                           if get_obj_base_key(obj) not in keys}
    if collector.protected:
        raise ProtectedError('The objects are referenced through a protected '
                             'foreign key.', collector.protected)
    for related_object in chain(
            *collector.data.values(),
            (related_object for model in apps.get_models()
             for related_object, obj in chain(
                ModelRichTextCollector(model,
                                       using=using).find_objects(*objects),
                ModelStreamFieldsCollector(model,
                                           using=using).find_objects(*objects)))):
        key = get_obj_base_key(related_object)
        if key not in keys:
            yield related_object
            keys.add(key)


def get_paginated_uses(request, *objects, using=DEFAULT_DB_ALIAS):
    try:
        page = paginate(request, list(get_all_uses(*objects, using=using)))[1]
    except ProtectedError as e:
        page = paginate(request, list(e.protected_objects))[1]
        page.are_protected = True
    else:
        page.are_protected = False
    return page
