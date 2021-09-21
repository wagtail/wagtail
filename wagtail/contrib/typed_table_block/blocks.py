from django import forms
from django.utils.functional import cached_property

from wagtail.admin.staticfiles import versioned_static
from wagtail.core.blocks.base import Block, DeclarativeSubBlocksMetaclass, get_help_icon
from wagtail.core.telepath import Adapter, register


class BaseTypedTableBlock(Block):
    def __init__(self, local_blocks=None, **kwargs):
        self._constructor_kwargs = kwargs

        super().__init__(**kwargs)

        # create a local (shallow) copy of base_blocks so that it can be supplemented by local_blocks
        self.child_blocks = self.base_blocks.copy()
        if local_blocks:
            for name, block in local_blocks:
                block.set_name(name)
                self.child_blocks[name] = block

    def value_from_datadict(self, data, files, prefix):
        column_count = int(data['%s-column-count' % prefix])
        columns = [
            {
                'id': i,
                'type': data['%s-column-%d-type' % (prefix, i)],
                'order': int(data['%s-column-%d-order' % (prefix, i)]),
                'heading': data['%s-column-%d-heading' % (prefix, i)],
            }
            for i in range(0, column_count)
            if not data['%s-column-%d-deleted' % (prefix, i)]
        ]
        columns.sort(key=lambda col: col['order'])
        for col in columns:
            col['block'] = self.child_blocks[col['type']]

        row_count = int(data['%s-row-count' % prefix])
        rows = [
            {'values': [
                col['block'].value_from_datadict(
                    data, files, '%s-cell-%d-%d' % (prefix, row_index, col['id'])
                )
                for col in columns
            ]}
            for row_index in range(0, row_count)
        ]

        return {
            'columns': [
                {
                    'block': col['block'],
                    'heading': col['heading']
                }
                for col in columns
            ],
            'rows': rows,
        }

    def get_prep_value(self, value):
        if value:
            return {
                'columns': [
                    {'type': col['block'].name, 'heading': col['heading']}
                    for col in value['columns']
                ],
                'rows': [
                    {
                        'values': [
                            col['block'].get_prep_value(row['values'][i])
                            for i, col in enumerate(value['columns'])
                        ]
                    }
                    for row in value['rows']
                ]
            }
        else:
            return {
                'columns': [],
                'rows': [],
            }

    def to_python(self, value):
        if value:
            columns = [
                {
                    'block': self.child_blocks[col['type']],
                    'heading': col['heading'],
                }
                for col in value['columns']
            ]
            # restore data column-by-column to take advantage of bulk_to_python
            columns_data = [
                col['block'].bulk_to_python([
                    row['values'][column_index] for row in value['rows']
                ])
                for column_index, col in enumerate(columns)
            ]
            return {
                'columns': columns,
                'rows': [
                    {
                        'values': [
                            column_data[row_index]
                            for column_data in columns_data
                        ]
                    }
                    for row_index in range(0, len(value['rows']))
                ]
            }
        else:
            return {
                'columns': [],
                'rows': [],
            }

    def get_form_state(self, value):
        if value:
            return {
                'columns': [
                    {'type': col['block'].name, 'heading': col['heading']}
                    for col in value['columns']
                ],
                'rows': [
                    {
                        'values': [
                            col['block'].get_form_state(row['values'][column_index])
                            for column_index, col in enumerate(value['columns'])
                        ]
                    }
                    for row in value['rows']
                ]
            }
        else:
            return {
                'columns': [],
                'rows': [],
            }

    def deconstruct(self):
        """
        Always deconstruct TypedTableBlock instances as if they were plain TypedTableBlock with all
        of the field definitions passed to the constructor - even if in reality this is a subclass
        with the fields defined declaratively, or some combination of the two.

        This ensures that the field definitions get frozen into migrations, rather than leaving a
        reference to a custom subclass in the user's models.py that may or may not stick around.
        """
        path = 'wagtail.contrib.typed_table_block.blocks.TypedTableBlock'
        args = [list(self.child_blocks.items())]
        kwargs = self._constructor_kwargs
        return (path, args, kwargs)

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        for name, child_block in self.child_blocks.items():
            errors.extend(child_block.check(**kwargs))
            errors.extend(child_block._check_name(**kwargs))

        return errors

    class Meta:
        default = None
        icon = "table"


class TypedTableBlock(BaseTypedTableBlock, metaclass=DeclarativeSubBlocksMetaclass):
    pass


class TypedTableBlockAdapter(Adapter):
    js_constructor = 'wagtail.contrib.typed_table_block.blocks.TypedTableBlock'

    def js_args(self, block):
        meta = {
            'label': block.label, 'required': block.required, 'icon': block.meta.icon,
        }

        help_text = getattr(block.meta, 'help_text', None)
        if help_text:
            meta['helpText'] = help_text
            meta['helpIcon'] = get_help_icon()

        return [
            block.name,
            block.child_blocks.values(),
            {
                name: child_block.get_form_state(child_block.get_default())
                for name, child_block in block.child_blocks.items()
            },
            meta,
        ]

    @cached_property
    def media(self):
        return forms.Media(js=[
            versioned_static('typed_table_block/js/typed_table_block.js'),
        ])


register(TypedTableBlockAdapter(), TypedTableBlock)
