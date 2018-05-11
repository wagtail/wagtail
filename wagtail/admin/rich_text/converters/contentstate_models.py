import json
import random
import string

ALPHANUM = string.ascii_lowercase + string.digits


class Block(object):
    def __init__(self, typ, depth=0):
        self.type = typ
        self.depth = depth
        self.text = ""
        self.key = ''.join(random.choice(ALPHANUM) for _ in range(5))
        self.inline_style_ranges = []
        self.entity_ranges = []

    def as_dict(self):
        return {
            'key': self.key,
            'type': self.type,
            'depth': self.depth,
            'text': self.text,
            'inlineStyleRanges': [isr.as_dict() for isr in self.inline_style_ranges],
            'entityRanges': [er.as_dict() for er in self.entity_ranges],
        }


class InlineStyleRange(object):
    def __init__(self, style):
        self.style = style
        self.offset = None
        self.length = None

    def as_dict(self):
        return {
            'offset': self.offset,
            'length': self.length,
            'style': self.style,
        }


class Entity(object):
    def __init__(self, entity_type, mutability, data):
        self.entity_type = entity_type
        self.mutability = mutability
        self.data = data

    def as_dict(self):
        return {
            'mutability': self.mutability,
            'type': self.entity_type,
            'data': self.data,
        }


class EntityRange(object):
    def __init__(self, key):
        self.key = key
        self.offset = None
        self.length = None

    def as_dict(self):
        return {
            'key': self.key,
            'offset': self.offset,
            'length': self.length,
        }


class ContentState(object):
    """Pythonic representation of a draft.js contentState structure"""
    def __init__(self):
        self.blocks = []
        self.entity_count = 0
        self.entity_map = {}

    def add_entity(self, entity):
        key = self.entity_count
        self.entity_map[key] = entity
        self.entity_count += 1
        return key

    def as_dict(self):
        return {
            'blocks': [block.as_dict() for block in self.blocks],
            'entityMap': {key: entity.as_dict() for (key, entity) in self.entity_map.items()},
        }

    def as_json(self, **kwargs):
        return json.dumps(self.as_dict(), **kwargs)
