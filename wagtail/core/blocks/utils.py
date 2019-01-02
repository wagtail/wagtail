import json

from django.core.serializers.json import DjangoJSONEncoder


class ConfigJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, BlockData):
            return o.data
        return super().default(o)


class InputJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, BlockData):
            return {'id': o['id'],
                    'type': o['type'],
                    'value': o['value']}
        return super().default(o)


def to_json_script(data, encoder=ConfigJSONEncoder):
    return json.dumps(
        data, separators=(',', ':'), cls=encoder
    ).replace('<', '\\u003c')


class BlockData:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __repr__(self):
        return '<BlockData %s>' % self.data
