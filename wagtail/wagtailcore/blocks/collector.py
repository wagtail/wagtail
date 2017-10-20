from __future__ import absolute_import, unicode_literals

import re
from warnings import warn

from django.apps import apps
from django.db.models import Model, Q

from wagtail.wagtailcore.blocks import ListBlock, StreamBlock, StreamValue, StructBlock, StructValue
from wagtail.wagtailcore.fields import StreamField


class StreamFieldCollector:
    def __init__(self, field):
        self.field = field

    def find_block_type(self, block_type, blocks=None, block_path=None):
        if blocks is None:
            blocks = [self.field.stream_block]
        if block_path is None:
            block_path = [self.field.stream_block]
        for block in blocks:
            current_path = block_path + [block]
            if isinstance(block, block_type):
                return current_path
            elif isinstance(block, (StreamBlock, StructBlock)):
                return self.find_block_type(
                    block_type, block.child_blocks.values(),
                    block_path=current_path)
            elif isinstance(block, ListBlock):
                return self.find_block_type(block_type, [block.child_block],
                                            block_path=current_path)

    def find_values(self, value, block_path):
        block_path = block_path[1:]
        if len(block_path) == 1:
            last_block = block_path[0]
            if isinstance(value, StreamValue.StreamChild):
                if last_block.name == value.block.name:
                    yield value.value
            elif isinstance(value, StructValue):
                if last_block.name in value:
                    yield value[last_block.name]
        else:
            if isinstance(value, StreamValue):
                for item in value:
                    yield from self.find_values(item, block_path)
            elif isinstance(value, StreamValue.StreamChild):
                if value.block.name == value.block.name:
                    yield from self.find_values(value.value, block_path)
            else:
                warn('Unexpected StreamField value: <%s: %s>'
                     % (type(value), str(value)[:30]))


class ModelStreamFieldsCollector:
    def __init__(self, model):
        self.model = model
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
        if isinstance(value, None):
            return 'null'
        return '"%s"' % re.escape(str(value).replace('"', r'\"')
                                  .replace('|', r'\|'))

    def find_objects_for(self, block_type, searched_values=()):
        if not self.fields:
            return
        block_paths_per_field = [c.find_block_type(block_type)
                                 for c in self.field_collectors]
        filters = Q()
        for field, block_path in zip(self.fields, block_paths_per_field):
            block_filter = Q(**{field.attname + '__regex': r'"(%s)"'
                                % '|'.join([block.name for block in block_path
                                            if getattr(block, 'name', '')])})
            value_filter = (
                Q(**{field.attname + '__regex': '(%s)'
                     % '|'.join(self.prepare_value(v)
                                for v in searched_values)})
                if searched_values else Q())
            filters |= block_filter & value_filter
        for obj in self.model._default_manager.filter(filters):
            for collector, block_path in zip(self.field_collectors,
                                             block_paths_per_field):
                for found_value in collector.find_values(
                        getattr(obj, collector.field.attname), block_path):
                    if not searched_values or found_value in searched_values:
                        yield obj, found_value


def get_all_uses(block_type, searched_values=()):
    for model in apps.get_models():
        yield from ModelStreamFieldsCollector(model).find_objects_for(
            block_type, searched_values=searched_values)
