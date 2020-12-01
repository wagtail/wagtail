from .base import Block


__all__ = ['StaticBlock']


class StaticBlock(Block):
    """
    A block that just 'exists' and has no fields.
    """
    def value_from_datadict(self, data, files, prefix):
        return None

    class Meta:
        admin_text = None
        default = None
