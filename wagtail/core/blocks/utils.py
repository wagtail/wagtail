import json

from django.core.exceptions import NON_FIELD_ERRORS
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.utils import ErrorList


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


def get_non_block_errors(errors):
    if errors is None:
        return ()
    errors_data = errors.as_data()
    if isinstance(errors, ErrorList):
        errors_data = errors_data[0].params
        if errors_data is None:
            return errors
    if isinstance(errors_data, dict):
        return errors_data.get(NON_FIELD_ERRORS, ())
    return ()


class BlockData:
    def __init__(self, data):
        self.data = data

    def __contains__(self, item):
        return item in self.data

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __repr__(self):
        return '<BlockData %s>' % self.data
