import re
from warnings import warn

from django.apps import apps
from django.db.models import Model, Q

from wagtail.core.blocks import ListBlock, StreamBlock, StreamValue, StructBlock, StructValue
from wagtail.core.fields import StreamField


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

    def find_block_type(self, block_type):
        for block_path in self.block_tree_paths(self.field.stream_block):
            if isinstance(block_path[-1], block_type):
                yield block_path

    def find_values(self, stream, block_path):
        if not block_path:
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
        if value is None:
            return 'null'
        return '"%s"' % re.escape(str(value).replace('"', r'\"')
                                  .replace('|', r'\|'))

    def find_objects_for(self, block_type, searched_values=()):
        if not self.fields:
            return
        block_paths_per_field = [list(c.find_block_type(block_type))
                                 for c in self.field_collectors]
        filters = Q()
        for field, block_paths in zip(self.fields, block_paths_per_field):
            last_blocks = [[block for block in block_path if block.name][-1]
                           for block_path in block_paths]
            block_filter = Q(**{field.attname + '__regex': r'"(%s)"'
                                % '|'.join({block.name for block in last_blocks})})
            value_filter = (
                Q(**{field.attname + '__regex': r'(%s)'
                     % '|'.join(self.prepare_value(v)
                                for v in searched_values)})
                if searched_values else Q())
            filters |= block_filter & value_filter
        for obj in self.model._default_manager.filter(filters):
            for collector, block_paths in zip(self.field_collectors,
                                              block_paths_per_field):
                for block_path in block_paths:
                    for found_value in collector.find_values(
                            getattr(obj, collector.field.attname), block_path):
                        if not searched_values or found_value in searched_values:
                            yield obj, found_value


def get_all_uses(block_type, searched_values=()):
    for model in apps.get_models():
        yield from ModelStreamFieldsCollector(model).find_objects_for(
            block_type, searched_values=searched_values)
