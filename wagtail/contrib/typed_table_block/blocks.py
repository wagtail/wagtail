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
